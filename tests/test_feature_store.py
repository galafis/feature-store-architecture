'''
Testes unitários para a Feature Store
Author: Gabriel Demetrios Lafis
Year: 2025
'''

import unittest
import sys
import os

# Adicionar o diretório src ao path para importar os módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from feature_store import (
    FeatureStore,
    Feature,
    FeatureMetadata,
    FeatureType,
    FeatureStatus,
    FeatureValidation
)


class TestFeatureStore(unittest.TestCase):
    '''Testes para a classe FeatureStore'''

    def setUp(self):
        '''Configuração executada antes de cada teste'''
        self.fs = FeatureStore(name="test-fs")

        # Criar uma feature de exemplo para os testes
        self.feature1 = Feature(
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

        # Criar uma segunda feature para testes de listagem
        self.feature2 = Feature(
            metadata=FeatureMetadata(
                name="customer_segment",
                description="Segmento do cliente",
                feature_type=FeatureType.CATEGORICAL,
                entity="customer",
                owner="test-team",
                status=FeatureStatus.ACTIVE
            ),
            validation=FeatureValidation(allowed_values=["bronze", "silver", "gold"])
        )

    def test_register_feature(self):
        '''Testa o registro de uma nova feature'''
        result = self.fs.register_feature(self.feature1)
        self.assertTrue(result)
        self.assertIn(self.feature1.metadata.name, [f['name'] for f in self.fs.list_features()])

    def test_register_duplicate_feature(self):
        '''Testa o registro de uma feature duplicada'''
        self.fs.register_feature(self.feature1)
        result = self.fs.register_feature(self.feature1)
        self.assertFalse(result)  # Não deve registrar a mesma feature duas vezes

    def test_get_feature(self):
        '''Testa a busca de uma feature'''
        self.fs.register_feature(self.feature1)
        retrieved_feature = self.fs.get_feature("total_purchases", "customer")
        self.assertIsNotNone(retrieved_feature)
        self.assertEqual(retrieved_feature.metadata.name, "total_purchases")

    def test_get_non_existent_feature(self):
        '''Testa a busca de uma feature inexistente'''
        retrieved_feature = self.fs.get_feature("non_existent", "customer")
        self.assertIsNone(retrieved_feature)

    def test_list_features(self):
        '''Testa a listagem de features'''
        self.fs.register_feature(self.feature1)
        self.fs.register_feature(self.feature2)
        features_list = self.fs.list_features()
        self.assertEqual(len(features_list), 2)
        feature_names = [f['name'] for f in features_list]
        self.assertIn("total_purchases", feature_names)
        self.assertIn("customer_segment", feature_names)

    def test_get_online_features(self):
        '''Testa a busca de features para inferência online'''
        self.fs.register_feature(self.feature1)
        # Simular a computação e armazenamento de um valor
        self.feature1.compute("CUST001", {"total_purchases": 10})
        
        online_features = self.fs.get_online_features(
            entity_id="CUST001",
            feature_names=["total_purchases"],
            entity="customer"
        )
        self.assertIn("total_purchases", online_features)
        self.assertEqual(online_features["total_purchases"], 10)

    def test_get_historical_features(self):
        '''Testa a busca de features históricas'''
        self.fs.register_feature(self.feature1)
        # Simular o histórico de valores
        self.feature1.compute("CUST001", {"total_purchases": 5})
        self.feature1.compute("CUST001", {"total_purchases": 10})

        historical_features = self.fs.get_historical_features(
            entity_ids=["CUST001"],
            feature_names=["total_purchases"],
            entity="customer"
        )
        self.assertEqual(len(historical_features), 1)
        self.assertEqual(len(historical_features[0]["total_purchases"]), 2)
        self.assertEqual(historical_features[0]["total_purchases"][1]['value'], 10)

    def test_feature_validation_success(self):
        '''Testa a validação de uma feature com sucesso'''
        # O valor 10 é válido (min_value=0)
        self.assertTrue(self.feature1._validate_value(10))

    def test_feature_validation_failure(self):
        '''Testa a falha na validação de uma feature'''
        # O valor -5 é inválido (min_value=0)
        self.assertFalse(self.feature1._validate_value(-5))

    def test_get_statistics(self):
        '''Testa a obtenção de estatísticas'''
        self.fs.register_feature(self.feature1)
        self.fs.register_feature(self.feature2)
        stats = self.fs.get_statistics()
        self.assertEqual(stats["total_features"], 2)
        self.assertEqual(stats["features_by_entity"], {"customer": 2})
        self.assertEqual(stats["features_by_status"], {"active": 2})
        self.assertEqual(stats["features_by_type"], {"numerical": 1, "categorical": 1})


if __name__ == '__main__':
    unittest.main(verbosity=2)

