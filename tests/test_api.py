"""
Testes para a API de Serving de Features
Author: Gabriel Demetrios Lafis
Year: 2025
"""

import unittest
import sys
import os
from datetime import datetime
import json
import redis

# Adicionar o diretório src ao path para importar os módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from feature_store import (
    FeatureStore,
    Feature,
    FeatureMetadata,
    FeatureType,
    FeatureStatus,
    FeatureGroup
)
from feature_serving_api import create_app


# Mock Redis para testes
class MockRedis:
    def __init__(self, host='localhost', port=6379, db=0, decode_responses=True, **kwargs):
        self.data = {}
        self.host = host
        self.port = port
        self.db = db
        self.decode_responses = decode_responses

    def hmset(self, key, mapping):
        self.data[key] = {k: str(v) for k, v in mapping.items()}

    def hgetall(self, key):
        return self.data.get(key, {})

    def flushdb(self):
        self.data = {}


class TestFeatureServingAPI(unittest.TestCase):
    """Testes para a API REST de serving de features"""

    def setUp(self):
        """Configuração executada antes de cada teste"""
        # Mock Redis
        self.original_redis = redis.Redis
        redis.Redis = MockRedis

        self.offline_store_test_path = './test_offline_store_api'
        if os.path.exists(self.offline_store_test_path):
            import shutil
            shutil.rmtree(self.offline_store_test_path)
        os.makedirs(self.offline_store_test_path, exist_ok=True)

        # Criar Feature Store
        self.fs = FeatureStore(
            name="test-api-fs",
            offline_store_path=self.offline_store_test_path
        )
        self.fs.online_store.flushdb()

        # Criar Feature Group de teste
        test_fg = FeatureGroup(
            name="test_features",
            entity="test_entity",
            description="Features para teste da API"
        )
        
        test_feature = Feature(
            metadata=FeatureMetadata(
                name="test_value",
                description="Valor de teste",
                feature_type=FeatureType.NUMERICAL,
                entity="test_entity",
                owner="test@example.com",
                status=FeatureStatus.ACTIVE
            )
        )
        
        test_fg.add_feature(test_feature)
        self.fs.register_feature_group(test_fg)

        # Criar aplicação Flask
        self.app = create_app(self.fs)
        self.app.testing = True
        self.client = self.app.test_client()

    def tearDown(self):
        """Limpeza após cada teste"""
        redis.Redis = self.original_redis
        import shutil
        if os.path.exists(self.offline_store_test_path):
            shutil.rmtree(self.offline_store_test_path)

    def test_health_endpoint(self):
        """Testa o endpoint de health check"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'feature-serving-api')
        self.assertIn('timestamp', data)

    def test_list_groups(self):
        """Testa listagem de feature groups"""
        response = self.client.get('/groups')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('groups', data)
        self.assertEqual(len(data['groups']), 1)
        self.assertEqual(data['groups'][0]['name'], 'test_features')
        self.assertEqual(data['groups'][0]['entity'], 'test_entity')

    def test_list_all_features(self):
        """Testa listagem de todas as features"""
        response = self.client.get('/features')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('features', data)
        self.assertEqual(len(data['features']), 1)
        self.assertEqual(data['features'][0]['name'], 'test_value')
        self.assertEqual(data['features'][0]['type'], 'numerical')

    def test_get_feature_metadata(self):
        """Testa busca de metadados de feature"""
        response = self.client.get('/features/test_entity/test_value/metadata')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'test_value')
        self.assertEqual(data['type'], 'numerical')
        self.assertEqual(data['entity'], 'test_entity')
        self.assertEqual(data['owner'], 'test@example.com')

    def test_get_feature_metadata_not_found(self):
        """Testa busca de metadados de feature inexistente"""
        response = self.client.get('/features/test_entity/nonexistent/metadata')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_ingest_and_retrieve(self):
        """Testa ingestão e recuperação de features via API"""
        # Ingerir
        entity_id = "TEST001"
        test_data = {"test_value": 42.5}
        
        response = self.client.post(
            f'/ingest/test_features/{entity_id}',
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['group_name'], 'test_features')
        self.assertEqual(data['entity_id'], entity_id)

        # Recuperar
        response = self.client.get(f'/features/test_features/{entity_id}')
        self.assertEqual(response.status_code, 200)
        features = json.loads(response.data)
        self.assertEqual(float(features['test_value']), 42.5)

    def test_get_features_with_filter(self):
        """Testa busca de features específicas com filtro"""
        # Primeiro ingerir
        entity_id = "TEST002"
        self.client.post(
            f'/ingest/test_features/{entity_id}',
            json={"test_value": 100}
        )

        # Buscar com filtro
        response = self.client.get(
            f'/features/test_features/{entity_id}?features=test_value'
        )
        self.assertEqual(response.status_code, 200)
        features = json.loads(response.data)
        self.assertIn('test_value', features)

    def test_get_features_nonexistent_group(self):
        """Testa busca de features em grupo inexistente"""
        response = self.client.get('/features/nonexistent_group/ENTITY001')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('not found', data['error'].lower())

    def test_get_features_nonexistent_entity(self):
        """Testa busca de features para entidade inexistente"""
        response = self.client.get('/features/test_features/NONEXISTENT')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_ingest_invalid_group(self):
        """Testa ingestão em grupo inexistente"""
        response = self.client.post(
            '/ingest/nonexistent_group/ENTITY001',
            json={"test_value": 123}
        )
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_ingest_no_data(self):
        """Testa ingestão sem dados"""
        response = self.client.post('/ingest/test_features/ENTITY001')
        # Flask retorna 415 (Unsupported Media Type) quando não há Content-Type
        # ou 400 quando há Content-Type mas sem dados
        self.assertIn(response.status_code, [400, 415])

    def test_ingest_invalid_json(self):
        """Testa ingestão com JSON inválido"""
        response = self.client.post(
            '/ingest/test_features/ENTITY001',
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main(verbosity=2)
