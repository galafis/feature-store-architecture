"""
Feature Store Architecture - Core Implementation
Author: Gabriel Demetrios Lafis
Year: 2025

Este módulo implementa uma Feature Store, um sistema centralizado para armazenamento,
gerenciamento e servimento de features (características) para modelos de Machine Learning.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json


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
    entity: str  # Entidade à qual a feature pertence (ex: "customer", "product")
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
    source_features: List[str]  # Features de entrada
    transformation_fn: Optional[Callable] = None  # Função de transformação
    sql_query: Optional[str] = None  # Query SQL alternativa


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
        self._values: Dict[str, Any] = {}  # entity_id -> value
        self._history: List[Dict[str, Any]] = []
    
    def compute(self, entity_id: str, source_data: Dict[str, Any]) -> Any:
        """
        Computa o valor da feature para uma entidade específica.
        """
        if self.transformation and self.transformation.transformation_fn:
            value = self.transformation.transformation_fn(source_data)
        else:
            # Se não há transformação, assume que o valor vem diretamente dos dados
            value = source_data.get(self.metadata.name)
        
        if not self._validate_value(value):
            raise ValueError(f"Valor inválido para feature '{self.metadata.name}': {value}")
        
        self._values[entity_id] = value
        self._log_computation(entity_id, value)
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
    
    def _log_computation(self, entity_id: str, value: Any):
        """Registra o cálculo da feature"""
        self._history.append({
            "entity_id": entity_id,
            "value": value,
            "timestamp": datetime.now(),
            "version": self.metadata.version
        })
    
    def get_value(self, entity_id: str) -> Optional[Any]:
        """Retorna o valor atual da feature para uma entidade"""
        return self._values.get(entity_id)
    
    def get_history(self, entity_id: str) -> List[Dict[str, Any]]:
        """Retorna o histórico de valores para uma entidade"""
        return [h for h in self._history if h["entity_id"] == entity_id]


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
                f"Feature entity '{feature.metadata.entity}' não corresponde "
                f"ao entity do grupo '{self.entity}'"
            )
        self.features[feature.metadata.name] = feature
    
    def compute_all(self, entity_id: str, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Computa todas as features do grupo para uma entidade"""
        results = {}
        for feature_name, feature in self.features.items():
            try:
                results[feature_name] = feature.compute(entity_id, source_data)
            except Exception as e:
                print(f"Erro ao computar feature '{feature_name}': {e}")
                results[feature_name] = None
        return results
    
    def get_feature_vector(self, entity_id: str) -> Dict[str, Any]:
        """Retorna o vetor de features para uma entidade"""
        return {
            feature_name: feature.get_value(entity_id)
            for feature_name, feature in self.features.items()
        }


class FeatureStore:
    """
    Feature Store - Sistema centralizado para gerenciamento de features.
    
    Funcionalidades:
    1. Registro e versionamento de features
    2. Computação e armazenamento de features
    3. Servimento de features para treinamento e inferência
    4. Monitoramento e observabilidade
    """
    
    def __init__(self, name: str):
        self.name = name
        self.features: Dict[str, Feature] = {}
        self.feature_groups: Dict[str, FeatureGroup] = {}
        self._registry: Dict[str, Dict[str, Any]] = {}
        self.created_at = datetime.now()
    
    def register_feature(self, feature: Feature) -> bool:
        """Registra uma nova feature na Feature Store"""
        feature_id = self._generate_feature_id(feature)
        
        if feature_id in self.features:
            print(f"⚠ Feature '{feature.metadata.name}' já está registrada")
            return False
        
        self.features[feature_id] = feature
        self._registry[feature_id] = {
            "metadata": feature.metadata,
            "registered_at": datetime.now()
        }
        
        print(f"✓ Feature '{feature.metadata.name}' registrada com sucesso")
        return True
    
    def register_feature_group(self, feature_group: FeatureGroup) -> bool:
        """Registra um grupo de features"""
        if feature_group.name in self.feature_groups:
            print(f"⚠ Feature Group '{feature_group.name}' já está registrado")
            return False
        
        self.feature_groups[feature_group.name] = feature_group
        
        # Registrar todas as features do grupo
        for feature in feature_group.features.values():
            self.register_feature(feature)
        
        print(f"✓ Feature Group '{feature_group.name}' registrado com sucesso")
        return True
    
    def _generate_feature_id(self, feature: Feature) -> str:
        """Gera um ID único para a feature"""
        unique_string = f"{feature.metadata.name}:{feature.metadata.entity}:{feature.metadata.version}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]
    
    def get_feature(self, feature_name: str, entity: str) -> Optional[Feature]:
        """Busca uma feature pelo nome e entidade"""
        for feature_id, feature in self.features.items():
            if (feature.metadata.name == feature_name and 
                feature.metadata.entity == entity):
                return feature
        return None
    
    def get_feature_group(self, group_name: str) -> Optional[FeatureGroup]:
        """Busca um grupo de features pelo nome"""
        return self.feature_groups.get(group_name)
    
    def get_online_features(
        self,
        entity_id: str,
        feature_names: List[str],
        entity: str
    ) -> Dict[str, Any]:
        """
        Retorna features para inferência online (baixa latência).
        """
        results = {}
        for feature_name in feature_names:
            feature = self.get_feature(feature_name, entity)
            if feature:
                results[feature_name] = feature.get_value(entity_id)
            else:
                results[feature_name] = None
        return results
    
    def get_historical_features(
        self,
        entity_ids: List[str],
        feature_names: List[str],
        entity: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna features históricas para treinamento de modelos.
        """
        results = []
        for entity_id in entity_ids:
            entity_features = {"entity_id": entity_id}
            for feature_name in feature_names:
                feature = self.get_feature(feature_name, entity)
                if feature:
                    history = feature.get_history(entity_id)
                    # Filtrar por data se especificado
                    if start_date or end_date:
                        history = [
                            h for h in history
                            if (not start_date or h["timestamp"] >= start_date) and
                               (not end_date or h["timestamp"] <= end_date)
                        ]
                    entity_features[feature_name] = history
            results.append(entity_features)
        return results
    
    def list_features(self, entity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista todas as features registradas"""
        features_list = []
        for feature_id, feature in self.features.items():
            if entity is None or feature.metadata.entity == entity:
                features_list.append({
                    "id": feature_id,
                    "name": feature.metadata.name,
                    "entity": feature.metadata.entity,
                    "type": feature.metadata.feature_type.value,
                    "status": feature.metadata.status.value,
                    "version": feature.metadata.version,
                    "owner": feature.metadata.owner
                })
        return features_list
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas da Feature Store"""
        return {
            "total_features": len(self.features),
            "total_feature_groups": len(self.feature_groups),
            "features_by_entity": self._count_by_entity(),
            "features_by_status": self._count_by_status(),
            "features_by_type": self._count_by_type()
        }
    
    def _count_by_entity(self) -> Dict[str, int]:
        """Conta features por entidade"""
        counts = {}
        for feature in self.features.values():
            entity = feature.metadata.entity
            counts[entity] = counts.get(entity, 0) + 1
        return counts
    
    def _count_by_status(self) -> Dict[str, int]:
        """Conta features por status"""
        counts = {}
        for feature in self.features.values():
            status = feature.metadata.status.value
            counts[status] = counts.get(status, 0) + 1
        return counts
    
    def _count_by_type(self) -> Dict[str, int]:
        """Conta features por tipo"""
        counts = {}
        for feature in self.features.values():
            ftype = feature.metadata.feature_type.value
            counts[ftype] = counts.get(ftype, 0) + 1
        return counts


def example_usage():
    """Exemplo de uso da Feature Store"""
    
    # Criar Feature Store
    fs = FeatureStore(name="production-feature-store")
    
    # Criar um Feature Group para clientes
    customer_fg = FeatureGroup(
        name="customer_features",
        entity="customer",
        description="Features relacionadas a clientes"
    )
    
    # Definir features
    # Feature 1: Total de compras
    total_purchases_feature = Feature(
        metadata=FeatureMetadata(
            name="total_purchases",
            description="Número total de compras do cliente",
            feature_type=FeatureType.NUMERICAL,
            entity="customer",
            owner="data-team@company.com",
            tags=["customer", "purchases"],
            status=FeatureStatus.ACTIVE
        ),
        validation=FeatureValidation(min_value=0)
    )
    
    # Feature 2: Valor médio de compra
    avg_purchase_value_feature = Feature(
        metadata=FeatureMetadata(
            name="avg_purchase_value",
            description="Valor médio das compras do cliente",
            feature_type=FeatureType.NUMERICAL,
            entity="customer",
            owner="data-team@company.com",
            tags=["customer", "purchases", "value"],
            status=FeatureStatus.ACTIVE
        ),
        transformation=FeatureTransformation(
            name="calculate_avg_purchase",
            description="Calcula a média de valor das compras",
            source_features=["total_purchases", "total_spent"],
            transformation_fn=lambda data: data["total_spent"] / data["total_purchases"] if data["total_purchases"] > 0 else 0
        ),
        validation=FeatureValidation(min_value=0)
    )
    
    # Feature 3: Segmento do cliente
    customer_segment_feature = Feature(
        metadata=FeatureMetadata(
            name="customer_segment",
            description="Segmento do cliente baseado em comportamento",
            feature_type=FeatureType.CATEGORICAL,
            entity="customer",
            owner="data-team@company.com",
            tags=["customer", "segment"],
            status=FeatureStatus.ACTIVE
        ),
        validation=FeatureValidation(
            allowed_values=["bronze", "silver", "gold", "platinum"]
        )
    )
    
    # Adicionar features ao grupo
    customer_fg.add_feature(total_purchases_feature)
    customer_fg.add_feature(avg_purchase_value_feature)
    customer_fg.add_feature(customer_segment_feature)
    
    # Registrar o Feature Group
    fs.register_feature_group(customer_fg)
    
    # Computar features para clientes
    print("\n📊 Computando features para clientes:")
    customers_data = [
        {
            "customer_id": "CUST001",
            "total_purchases": 15,
            "total_spent": 1500.00,
            "customer_segment": "gold"
        },
        {
            "customer_id": "CUST002",
            "total_purchases": 5,
            "total_spent": 250.00,
            "customer_segment": "silver"
        }
    ]
    
    for customer_data in customers_data:
        customer_id = customer_data["customer_id"]
        features = customer_fg.compute_all(customer_id, customer_data)
        print(f"  Cliente {customer_id}: {features}")
    
    # Buscar features online (inferência)
    print("\n🔍 Buscando features online para CUST001:")
    online_features = fs.get_online_features(
        entity_id="CUST001",
        feature_names=["total_purchases", "avg_purchase_value", "customer_segment"],
        entity="customer"
    )
    print(f"  {online_features}")
    
    # Listar features
    print("\n📋 Features registradas:")
    features_list = fs.list_features()
    for feature in features_list:
        print(f"  - {feature['name']} ({feature['type']}) - {feature['status']}")
    
    # Estatísticas
    print("\n📈 Estatísticas da Feature Store:")
    stats = fs.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    print("=" * 80)
    print("Feature Store Architecture - Example Usage")
    print("=" * 80)
    example_usage()
