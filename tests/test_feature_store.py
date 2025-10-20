
"""
Testes unitários para a Feature Store
Author: Gabriel Demetrios Lafis
Year: 2025
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
import json
import pandas as pd
import redis
import pyarrow.parquet as pq

# Adicionar o diretório src ao path para importar os módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from feature_store import (
    FeatureStore,
    Feature,
    FeatureMetadata,
    FeatureType,
    FeatureStatus,
    FeatureValidation,
    FeatureTransformation,
    FeatureGroup
)

# Mock Redis para testes
class MockRedis:
    def __init__(self, host='localhost', port=6379, db=0, decode_responses=True, **kwargs):
        self.data = {}
        self.host = host
        self.port = port
        self.db = db
        self.decode_responses = decode_responses

    def hmset(self, key, mapping):
        self.data[key] = {k: str(v) for k, v in mapping.items()} # Redis stores strings

    def hgetall(self, key):
        return self.data.get(key, {})

    def flushdb(self):
        self.data = {}


class TestFeatureStore(unittest.TestCase):
    """Testes para a classe FeatureStore"""

    def setUp(self):
        """Configuração executada antes de cada teste"""
        # Mock Redis
        self.original_redis = redis.Redis
        redis.Redis = MockRedis

        self.offline_store_test_path = './test_offline_store'
        if os.path.exists(self.offline_store_test_path):
            import shutil
            shutil.rmtree(self.offline_store_test_path)
        os.makedirs(self.offline_store_test_path, exist_ok=True)

        self.fs = FeatureStore(name="test-fs", offline_store_path=self.offline_store_test_path)
        self.fs.online_store.flushdb() # Limpar mock Redis

        # Definir features
        self.total_purchases_feature = Feature(
            metadata=FeatureMetadata(
                name="total_purchases",
                description="Número total de compras do cliente",
                feature_type=FeatureType.NUMERICAL,
                entity="customer",
                owner="test-team",
                status=FeatureStatus.ACTIVE
            ),
            validation=FeatureValidation(min_value=0)
        )
        
        self.avg_purchase_value_feature = Feature(
            metadata=FeatureMetadata(
                name="avg_purchase_value",
                description="Valor médio das compras do cliente",
                feature_type=FeatureType.NUMERICAL,
                entity="customer",
                owner="test-team",
                tags=["customer", "purchases", "value"],
                status=FeatureStatus.ACTIVE
            ),
            transformation=FeatureTransformation(
                name="calculate_avg_purchase",
                description="Calcula a média de valor das compras",
                source_features=["total_spent", "total_purchases"],
                transformation_fn=lambda data: data["total_spent"] / data["total_purchases"] if data["total_purchases"] > 0 else 0
            ),
            validation=FeatureValidation(min_value=0)
        )

        # Criar um Feature Group para clientes
        self.customer_fg = FeatureGroup(
            name="customer_features",
            entity="customer",
            description="Features relacionadas a clientes"
        )
        self.customer_fg.add_feature(self.total_purchases_feature)
        self.customer_fg.add_feature(self.avg_purchase_value_feature)
        self.fs.register_feature_group(self.customer_fg)

    def tearDown(self):
        """Limpeza após cada teste"""
        # Restaurar Redis original
        redis.Redis = self.original_redis
        # Limpar diretório de armazenamento offline
        import shutil
        if os.path.exists(self.offline_store_test_path):
            shutil.rmtree(self.offline_store_test_path)

    def test_register_feature_group(self):
        """Testa o registro de um Feature Group"""
        self.assertIn("customer_features", self.fs.feature_groups)
        self.assertEqual(len(self.fs.feature_groups["customer_features"].features), 2)

    def test_ingest_data_online_store(self):
        """Testa a ingestão de dados e armazenamento online"""
        entity_id = "CUST001"
        source_data = {"total_spent": 1500.00, "total_purchases": 15}
        timestamp = datetime.now()
        self.fs.ingest_data("customer_features", entity_id, source_data, timestamp)

        online_features = self.fs.get_online_features("customer_features", entity_id)
        self.assertIsNotNone(online_features)
        self.assertEqual(online_features["total_purchases"], "15") # Redis stores as string
        self.assertAlmostEqual(float(online_features["avg_purchase_value"]), 100.00)

    def test_ingest_data_offline_store(self):
        """Testa a ingestão de dados e armazenamento offline"""
        entity_id = "CUST002"
        source_data = {"total_spent": 250.00, "total_purchases": 5}
        timestamp = datetime(2025, 1, 15, 10, 0, 0)
        self.fs.ingest_data("customer_features", entity_id, source_data, timestamp)

        historical_features_df = self.fs.get_historical_features("customer_features", timestamp - timedelta(days=1), timestamp + timedelta(days=1))
        self.assertIsNotNone(historical_features_df)
        self.assertFalse(historical_features_df.empty)
        self.assertEqual(len(historical_features_df), 1)
        self.assertEqual(historical_features_df["entity_id"].iloc[0], entity_id)
        self.assertEqual(historical_features_df["total_purchases"].iloc[0], 5)
        self.assertAlmostEqual(historical_features_df["avg_purchase_value"].iloc[0], 50.00)

    def test_get_online_features_non_existent(self):
        """Testa a busca de features online para entidade inexistente"""
        features = self.fs.get_online_features("customer_features", "NONEXISTENT")
        self.assertEqual(features, {})

    def test_get_historical_features_no_data(self):
        """Testa a busca de features históricas sem dados"""
        historical_features_df = self.fs.get_historical_features("customer_features", datetime(2020, 1, 1), datetime(2020, 1, 2))
        self.assertIsNone(historical_features_df) # pq.ParquetDataset will raise if no files match filter

    def test_feature_validation_success(self):
        """Testa a validação de uma feature com sucesso"""
        self.assertTrue(self.total_purchases_feature._validate_value(10))

    def test_feature_validation_failure(self):
        """Testa a falha na validação de uma feature"""
        self.assertFalse(self.total_purchases_feature._validate_value(-5))

    def test_feature_transformation(self):
        """Testa a transformação de uma feature"""
        data = {"total_spent": 100.0, "total_purchases": 10}
        transformed_value = self.avg_purchase_value_feature.compute(data)
        self.assertAlmostEqual(transformed_value, 10.0)

        data_zero_purchases = {"total_spent": 100.0, "total_purchases": 0}
        transformed_value_zero = self.avg_purchase_value_feature.compute(data_zero_purchases)
        self.assertAlmostEqual(transformed_value_zero, 0.0)

    def test_flask_api_get_features(self):
        """Testa o endpoint GET /features/<group_name>/<entity_id> da API Flask"""
        try:
            from flask import Flask
        except ImportError:
            self.skipTest("Flask not installed")
            return

        app = self.fs.create_flask_app()
        app.testing = True
        client = app.test_client()

        entity_id = "CUST003"
        source_data = {"total_spent": 300.00, "total_purchases": 3}
        timestamp = datetime.now()
        self.fs.ingest_data("customer_features", entity_id, source_data, timestamp)

        response = client.get(f'/features/customer_features/{entity_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["total_purchases"], "3")
        self.assertAlmostEqual(float(data["avg_purchase_value"]), 100.00)

    def test_flask_api_ingest_data(self):
        """Testa o endpoint POST /ingest/<group_name>/<entity_id> da API Flask"""
        try:
            from flask import Flask
        except ImportError:
            self.skipTest("Flask not installed")
            return

        app = self.fs.create_flask_app()
        app.testing = True
        client = app.test_client()

        entity_id = "CUST004"
        source_data = {"total_spent": 400.00, "total_purchases": 4}

        response = client.post(f'/ingest/customer_features/{entity_id}', json=source_data)
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")

        # Verificar se os dados foram realmente ingeridos no online store
        online_features = self.fs.get_online_features("customer_features", entity_id)
        self.assertIsNotNone(online_features)
        self.assertEqual(online_features["total_purchases"], "4")


if __name__ == '__main__':
    unittest.main(verbosity=2)

