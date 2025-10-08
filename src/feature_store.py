
"""
Feature Store Architecture - Core Implementation
Author: Gabriel Demetrios Lafis
Year: 2025

Este módulo implementa uma Feature Store, um sistema centralizado para armazenamento,
gerenciamento e servimento de features (características) para modelos de Machine Learning.
Esta versão inclui armazenamento online (Redis), offline (Parquet) e uma API REST (Flask).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import os

# Dependências opcionais (instalar com `pip install redis flask`)
try:
    import redis
except ImportError:
    redis = None

try:
    from flask import Flask, jsonify, request
except ImportError:
    Flask = None


class FeatureType(Enum):
    """Tipos de features"""
    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    TEXT = "text"
    EMBEDDING = "embedding"


class FeatureStatus(Enum):
    """Status da feature"""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class FeatureMetadata:
    """Metadados de uma feature"""
    name: str
    description: str
    feature_type: FeatureType
    entity: str
    owner: str
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: FeatureStatus = FeatureStatus.DRAFT
    version: str = "1.0.0"


@dataclass
class FeatureTransformation:
    """Define uma transformação para calcular a feature"""
    name: str
    description: str
    source_features: List[str]
    transformation_fn: Optional[Callable] = None
    sql_query: Optional[str] = None


@dataclass
class FeatureValidation:
    """Regras de validação para a feature"""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None
    not_null: bool = True
    unique: bool = False


class Feature:
    """
    Representa uma feature individual na Feature Store.
    """
    
    def __init__(
        self,
        metadata: FeatureMetadata,
        transformation: Optional[FeatureTransformation] = None,
        validation: Optional[FeatureValidation] = None
    ):
        self.metadata = metadata
        self.transformation = transformation
        self.validation = validation or FeatureValidation()
    
    def compute(self, source_data: Dict[str, Any]) -> Any:
        """
        Computa o valor da feature para uma entidade específica.
        """
        if self.transformation and self.transformation.transformation_fn:
            value = self.transformation.transformation_fn(source_data)
        else:
            value = source_data.get(self.metadata.name)
        
        if not self._validate_value(value):
            raise ValueError(f"Valor inválido para feature \'{self.metadata.name}\': {value}")
        
        return value
    
    def _validate_value(self, value: Any) -> bool:
        """Valida o valor da feature"""
        if value is None and self.validation.not_null:
            return False
        
        if value is not None:
            if self.validation.min_value is not None and value < self.validation.min_value:
                return False
            if self.validation.max_value is not None and value > self.validation.max_value:
                return False
            if self.validation.allowed_values and value not in self.validation.allowed_values:
                return False
        
        return True


class FeatureGroup:
    """
    Agrupa features relacionadas que são computadas juntas.
    """
    
    def __init__(self, name: str, entity: str, description: str):
        self.name = name
        self.entity = entity
        self.description = description
        self.features: Dict[str, Feature] = {}
        self.created_at = datetime.now()
    
    def add_feature(self, feature: Feature):
        """Adiciona uma feature ao grupo"""
        if feature.metadata.entity != self.entity:
            raise ValueError(
                f"Feature entity \'{feature.metadata.entity}\' não corresponde "
                f"ao entity do grupo \'{self.entity}\'"
            )
        self.features[feature.metadata.name] = feature
    
    def compute_all(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Computa todas as features do grupo para uma entidade"""
        results = {}
        for feature_name, feature in self.features.items():
            try:
                results[feature_name] = feature.compute(source_data)
            except Exception as e:
                print(f"Erro ao computar feature \'{feature_name}\': {e}")
                results[feature_name] = None
        return results


class FeatureStore:
    """
    Feature Store - Sistema centralizado para gerenciamento de features.
    """
    
    def __init__(self, name: str, redis_host: str = 'localhost', redis_port: int = 6379, offline_store_path: str = './offline_store'):
        self.name = name
        self.feature_groups: Dict[str, FeatureGroup] = {}
        self.created_at = datetime.now()

        if redis:
            self.online_store = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
        else:
            self.online_store = None
            print("Aviso: Redis não está instalado. O armazenamento online estará desativado.")

        self.offline_store_path = offline_store_path
        os.makedirs(self.offline_store_path, exist_ok=True)
    
    def register_feature_group(self, feature_group: FeatureGroup) -> bool:
        """Registra um grupo de features"""
        if feature_group.name in self.feature_groups:
            print(f"⚠ Feature Group \'{feature_group.name}\' já está registrado")
            return False
        
        self.feature_groups[feature_group.name] = feature_group
        print(f"✓ Feature Group \'{feature_group.name}\' registrado com sucesso")
        return True

    def ingest_data(self, group_name: str, entity_id: str, source_data: Dict[str, Any], timestamp: datetime):
        """Ingere dados, computa features e armazena nos armazenamentos online e offline."""
        feature_group = self.feature_groups.get(group_name)
        if not feature_group:
            raise ValueError(f"Feature Group \'{group_name}\' não encontrado.")

        computed_features = feature_group.compute_all(source_data)
        computed_features["entity_id"] = entity_id
        computed_features["timestamp"] = timestamp.isoformat()

        # Armazenamento Online (Redis)
        if self.online_store:
            online_key = f"{group_name}:{entity_id}"
            self.online_store.hmset(online_key, computed_features)

        # Armazenamento Offline (Parquet)
        df = pd.DataFrame([computed_features])
        table = pa.Table.from_pandas(df)
        
        partition_cols = ["date"]
        df["date"] = timestamp.strftime("%Y-%m-%d")
        
        pq.write_to_dataset(
            table,
            root_path=os.path.join(self.offline_store_path, group_name),
            partition_cols=partition_cols
        )

    def get_online_features(self, group_name: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Retorna features para inferência online (baixa latência)."""
        if not self.online_store:
            print("Erro: Armazenamento online (Redis) não está disponível.")
            return None

        online_key = f"{group_name}:{entity_id}"
        return self.online_store.hgetall(online_key)

    def get_historical_features(self, group_name: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """Retorna features históricas para treinamento de modelos."""
        group_path = os.path.join(self.offline_store_path, group_name)
        if not os.path.exists(group_path):
            return None

        try:
            dataset = pq.ParquetDataset(group_path, filters=[
                ("date", ">=", start_date.strftime("%Y-%m-%d")),
                ("date", "<=", end_date.strftime("%Y-%m-%d"))
            ])
            return dataset.read().to_pandas()
        except Exception as e:
            print(f"Erro ao ler dados históricos: {e}")
            return None

    def create_flask_app(self):
        """Cria e retorna uma instância da aplicação Flask para a API REST."""
        if not Flask:
            raise ImportError("Flask não está instalado. Execute `pip install Flask`.")

        app = Flask(__name__)

        @app.route('/features/<group_name>/<entity_id>', methods=['GET'])
        def get_features(group_name, entity_id):
            features = self.get_online_features(group_name, entity_id)
            if features:
                return jsonify(features)
            return jsonify({"error": "Features não encontradas"}), 404

        @app.route('/ingest/<group_name>/<entity_id>', methods=['POST'])
        def ingest(group_name, entity_id):
            data = request.json
            if not data:
                return jsonify({"error": "Dados não fornecidos"}), 400
            
            try:
                self.ingest_data(group_name, entity_id, data, datetime.now())
                return jsonify({"status": "success"}), 201
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        return app


def example_usage():
    """Exemplo de uso da Feature Store com armazenamento online e offline."""
    
    fs = FeatureStore(name="production-feature-store")
    
    # Criar um Feature Group para clientes
    customer_fg = FeatureGroup(
        name="customer_features",
        entity="customer",
        description="Features relacionadas a clientes"
    )
    
    # Definir features
    total_purchases_feature = Feature(
        metadata=FeatureMetadata(name="total_purchases", description="Número total de compras", feature_type=FeatureType.NUMERICAL, entity="customer", owner="sales-team")
    )
    avg_purchase_value_feature = Feature(
        metadata=FeatureMetadata(name="avg_purchase_value", description="Valor médio de compra", feature_type=FeatureType.NUMERICAL, entity="customer", owner="sales-team"),
        transformation=FeatureTransformation(
            name="calculate_avg_purchase",
            description="Calcula a média de valor das compras",
            source_features=["total_spent", "total_purchases"],
            transformation_fn=lambda data: data["total_spent"] / data["total_purchases"] if data["total_purchases"] > 0 else 0
        )
    )
    
    customer_fg.add_feature(total_purchases_feature)
    customer_fg.add_feature(avg_purchase_value_feature)
    fs.register_feature_group(customer_fg)
    
    # Ingerir dados
    print("\n--- Ingerindo dados ---")
    customer_data = {
        "CUST001": {"total_spent": 1500.00, "total_purchases": 15},
        "CUST002": {"total_spent": 250.00, "total_purchases": 5}
    }
    for cust_id, data in customer_data.items():
        fs.ingest_data("customer_features", cust_id, data, datetime.now())
        print(f"Dados ingeridos para {cust_id}")

    # Obter features online
    print("\n--- Obtendo features online ---")
    online_features = fs.get_online_features("customer_features", "CUST001")
    print(f"Features online para CUST001: {online_features}")

    # Obter features históricas
    print("\n--- Obtendo features históricas ---")
    historical_features = fs.get_historical_features("customer_features", datetime.now() - timedelta(days=1), datetime.now())
    if historical_features is not None:
        print("Features históricas:")
        print(historical_features)

    # Iniciar a API REST (exemplo)
    print("\n--- Iniciando API REST em http://127.0.0.1:5000 ---")
    print("Para testar, use: curl http://127.0.0.1:5000/features/customer_features/CUST001")
    app = fs.create_flask_app()
    # Para executar em um ambiente de produção, use um servidor WSGI como Gunicorn ou uWSGI.
    # app.run(debug=True) # Descomente para rodar a API

if __name__ == "__main__":
    example_usage()

