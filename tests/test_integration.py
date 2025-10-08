import unittest
import sys
import os
from datetime import datetime, timedelta
import json
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
    def __init__(self):
        self.data = {}

    def hmset(self, key, mapping):
        self.data[key] = {k: str(v) for k, v in mapping.items()} # Redis stores strings

    def hgetall(self, key):
        return self.data.get(key, {})

    def flushdb(self):
        self.data = {}


class TestFeatureStoreIntegration(unittest.TestCase):
    """Testes de integração para a FeatureStore, incluindo a API Flask e persistência"""

    def setUp(self):
        # Mock Redis
        self.original_redis = redis.Redis
        redis.Redis = MockRedis

        self.offline_store_test_path = './test_offline_store_integration'
        if os.path.exists(self.offline_store_test_path):
            import shutil
            shutil.rmtree(self.offline_store_test_path)
        os.makedirs(self.offline_store_test_path, exist_ok=True)

        self.fs = FeatureStore(name="test-fs-integration", offline_store_path=self.offline_store_test_path)
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

        # Criar a aplicação Flask
        self.app = self.fs.create_flask_app()
        self.app.testing = True
        self.client = self.app.test_client()

    def tearDown(self):
        # Restaurar Redis original
        redis.Redis = self.original_redis
        # Limpar diretório de armazenamento offline
        import shutil
        if os.path.exists(self.offline_store_test_path):
            shutil.rmtree(self.offline_store_test_path)

    def test_ingest_and_retrieve_via_api(self):
        """Testa a ingestão de dados via API e a recuperação via API e diretamente da FeatureStore"""
        entity_id = "CUST_API_001"
        source_data = {"total_spent": 500.00, "total_purchases": 5}

        # 1. Ingestão via API
        ingest_response = self.client.post(f'/ingest/customer_features/{entity_id}', json=source_data)
        self.assertEqual(ingest_response.status_code, 201)
        ingest_data = json.loads(ingest_response.data)
        self.assertEqual(ingest_data["status"], "success")

        # 2. Recuperação online via API
        get_response = self.client.get(f'/features/customer_features/{entity_id}')
        self.assertEqual(get_response.status_code, 200)
        retrieved_api_data = json.loads(get_response.data)
        self.assertEqual(retrieved_api_data["total_purchases"], "5")
        self.assertAlmostEqual(float(retrieved_api_data["avg_purchase_value"]), 100.00)

        # 3. Recuperação online diretamente da FeatureStore (para verificar consistência)
        online_features_direct = self.fs.get_online_features("customer_features", entity_id)
        self.assertIsNotNone(online_features_direct)
        self.assertEqual(online_features_direct["total_purchases"], "5")
        self.assertAlmostEqual(float(online_features_direct["avg_purchase_value"]), 100.00)

        # 4. Verificar armazenamento offline (o timestamp é gerado internamente, então buscamos por um range)
        # Damos um pequeno tempo para garantir que o arquivo Parquet seja escrito
        # time.sleep(1) 
        # Para testes, é melhor mockar ou ter um mecanismo de flush explícito
        # Por enquanto, vamos assumir que a escrita é rápida o suficiente ou que o teste é executado em um ambiente que permite isso.
        # Ou, podemos buscar por um range amplo.
        start_time = datetime.now() - timedelta(minutes=1)
        end_time = datetime.now() + timedelta(minutes=1)
        historical_features_df = self.fs.get_historical_features("customer_features", start_time, end_time)
        self.assertIsNotNone(historical_features_df)
        self.assertFalse(historical_features_df.empty)
        self.assertEqual(historical_features_df["entity_id"].iloc[0], entity_id)
        self.assertEqual(historical_features_df["total_purchases"].iloc[0], 5)
        self.assertAlmostEqual(historical_features_df["avg_purchase_value"].iloc[0], 100.00)

    def test_ingest_invalid_data_via_api(self):
        """Testa a ingestão de dados inválidos via API"""
        entity_id = "CUST_API_002"
        invalid_source_data = {"total_spent": -100.00, "total_purchases": 10} # total_spent negativo

        ingest_response = self.client.post(f'/ingest/customer_features/{entity_id}', json=invalid_source_data)
        self.assertEqual(ingest_response.status_code, 400) # Espera-se um erro de validação
        ingest_data = json.loads(ingest_response.data)
        self.assertIn("error", ingest_data)
        self.assertIn("Validation failed for feature total_purchases", ingest_data["error"])

        # Verificar que os dados não foram armazenados
        online_features = self.fs.get_online_features("customer_features", entity_id)
        self.assertEqual(online_features, {})

    def test_get_features_non_existent_group_via_api(self):
        """Testa a busca de features para um grupo inexistente via API"""
        response = self.client.get('/features/non_existent_group/some_id')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn("error", data)
        self.assertIn("Feature group 'non_existent_group' not found", data["error"])

if __name__ == '__main__':
    unittest.main(verbosity=2)

