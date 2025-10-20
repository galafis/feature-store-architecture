"""
Testes para os geradores de exemplos do mundo real
Author: Gabriel Demetrios Lafis
Year: 2025
"""

import unittest
import sys
import os
import pandas as pd

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from real_world_examples import EcommerceFeatureGenerator, FinancialFeatureGenerator


class TestEcommerceFeatureGenerator(unittest.TestCase):
    """Testes para o gerador de features de e-commerce"""

    def setUp(self):
        """Configuração antes de cada teste"""
        self.generator = EcommerceFeatureGenerator()

    def test_generate_customer_features(self):
        """Testa geração de features de clientes"""
        num_customers = 100
        df = self.generator.generate_customer_features(num_customers)
        
        # Verificar shape
        self.assertEqual(len(df), num_customers)
        
        # Verificar colunas esperadas
        expected_columns = [
            'customer_id', 'age', 'gender', 'total_purchases',
            'total_spent', 'avg_order_value', 'days_since_last_purchase',
            'email_open_rate', 'app_sessions_per_week', 'favorite_category',
            'churn_probability', 'customer_tenure_days', 'timestamp'
        ]
        for col in expected_columns:
            self.assertIn(col, df.columns)
        
        # Verificar tipos de dados
        self.assertTrue(df['age'].dtype in [int, 'int64'])
        self.assertTrue(df['total_purchases'].dtype in [int, 'int64'])
        self.assertTrue(df['total_spent'].dtype in [float, 'float64'])
        
        # Verificar ranges válidos
        self.assertTrue((df['age'] >= 18).all())
        self.assertTrue((df['age'] <= 80).all())
        self.assertTrue((df['total_purchases'] >= 0).all())
        self.assertTrue((df['total_spent'] >= 0).all())
        self.assertTrue((df['email_open_rate'] >= 0).all())
        self.assertTrue((df['email_open_rate'] <= 1).all())
        self.assertTrue((df['churn_probability'] >= 0).all())
        self.assertTrue((df['churn_probability'] <= 1).all())
        
        # Verificar valores categóricos
        valid_genders = ['M', 'F', 'Other']
        self.assertTrue(df['gender'].isin(valid_genders).all())
        
        valid_categories = ['Electronics', 'Fashion', 'Home', 'Sports', 'Books']
        self.assertTrue(df['favorite_category'].isin(valid_categories).all())

    def test_generate_product_features(self):
        """Testa geração de features de produtos"""
        num_products = 50
        df = self.generator.generate_product_features(num_products)
        
        # Verificar shape
        self.assertEqual(len(df), num_products)
        
        # Verificar colunas esperadas
        expected_columns = [
            'product_id', 'category', 'price', 'view_count',
            'purchase_count', 'conversion_rate', 'avg_rating',
            'num_reviews', 'stock_quantity', 'days_in_stock',
            'discount_percentage', 'timestamp'
        ]
        for col in expected_columns:
            self.assertIn(col, df.columns)
        
        # Verificar ranges válidos
        self.assertTrue((df['price'] >= 10).all())
        self.assertTrue((df['price'] <= 5000).all())
        self.assertTrue((df['view_count'] >= 0).all())
        self.assertTrue((df['purchase_count'] >= 0).all())
        self.assertTrue((df['conversion_rate'] >= 0).all())
        self.assertTrue((df['conversion_rate'] <= 1).all())
        self.assertTrue((df['avg_rating'] >= 1).all())
        self.assertTrue((df['avg_rating'] <= 5).all())

    def test_generate_interaction_features(self):
        """Testa geração de features de interação"""
        customers_df = self.generator.generate_customer_features(10)
        products_df = self.generator.generate_product_features(5)
        num_interactions = 50
        
        df = self.generator.generate_interaction_features(
            customers_df, products_df, num_interactions
        )
        
        # Verificar shape
        self.assertEqual(len(df), num_interactions)
        
        # Verificar colunas esperadas
        expected_columns = [
            'interaction_id', 'customer_id', 'product_id',
            'interaction_type', 'device', 'session_duration_seconds',
            'timestamp'
        ]
        for col in expected_columns:
            self.assertIn(col, df.columns)
        
        # Verificar que customer_ids e product_ids são válidos
        self.assertTrue(df['customer_id'].isin(customers_df['customer_id']).all())
        self.assertTrue(df['product_id'].isin(products_df['product_id']).all())
        
        # Verificar valores categóricos
        valid_interactions = ['view', 'add_to_cart', 'purchase', 'wishlist']
        self.assertTrue(df['interaction_type'].isin(valid_interactions).all())
        
        valid_devices = ['mobile', 'desktop', 'tablet']
        self.assertTrue(df['device'].isin(valid_devices).all())

    def test_reproducibility(self):
        """Testa que os dados são reprodutíveis (seed fixo)"""
        df1 = self.generator.generate_customer_features(10)
        df2 = self.generator.generate_customer_features(10)
        
        # Com mesmo seed (42 no código), deve gerar mesmos dados
        pd.testing.assert_frame_equal(
            df1.drop('timestamp', axis=1),
            df2.drop('timestamp', axis=1)
        )


class TestFinancialFeatureGenerator(unittest.TestCase):
    """Testes para o gerador de features financeiras"""

    def setUp(self):
        """Configuração antes de cada teste"""
        self.generator = FinancialFeatureGenerator()

    def test_generate_transaction_features(self):
        """Testa geração de features de transações"""
        num_transactions = 100
        df = self.generator.generate_transaction_features(num_transactions)
        
        # Verificar shape
        self.assertEqual(len(df), num_transactions)
        
        # Verificar colunas esperadas
        expected_columns = [
            'transaction_id', 'account_id', 'amount',
            'transaction_type', 'country', 'hour_of_day',
            'is_international', 'is_high_amount', 'is_unusual_hour',
            'fraud_score', 'timestamp'
        ]
        for col in expected_columns:
            self.assertIn(col, df.columns)
        
        # Verificar tipos de dados
        self.assertTrue(df['amount'].dtype in [float, 'float64'])
        self.assertTrue(df['is_international'].dtype in [int, 'int64'])
        self.assertTrue(df['fraud_score'].dtype in [float, 'float64'])
        
        # Verificar ranges válidos
        self.assertTrue((df['amount'] >= 1).all())
        self.assertTrue((df['amount'] <= 10000).all())
        self.assertTrue((df['hour_of_day'] >= 0).all())
        self.assertTrue((df['hour_of_day'] <= 23).all())
        self.assertTrue((df['fraud_score'] >= 0).all())
        self.assertTrue((df['fraud_score'] <= 1).all())
        
        # Verificar valores binários
        self.assertTrue(df['is_international'].isin([0, 1]).all())
        self.assertTrue(df['is_high_amount'].isin([0, 1]).all())
        self.assertTrue(df['is_unusual_hour'].isin([0, 1]).all())
        
        # Verificar valores categóricos
        valid_types = ['purchase', 'withdrawal', 'transfer', 'payment']
        self.assertTrue(df['transaction_type'].isin(valid_types).all())
        
        valid_countries = ['BR', 'US', 'UK', 'DE', 'FR', 'JP', 'CN']
        self.assertTrue(df['country'].isin(valid_countries).all())

    def test_fraud_score_logic(self):
        """Testa que o fraud score tem lógica coerente"""
        df = self.generator.generate_transaction_features(1000)
        
        # Transações internacionais devem ter score maior em média
        international = df[df['is_international'] == 1]['fraud_score'].mean()
        domestic = df[df['is_international'] == 0]['fraud_score'].mean()
        self.assertGreater(international, domestic)
        
        # Transações de alto valor devem ter score maior em média (se houver ambos os tipos)
        high_amount_df = df[df['is_high_amount'] == 1]
        normal_amount_df = df[df['is_high_amount'] == 0]
        
        # Só comparar se houver dados em ambos os grupos
        if len(high_amount_df) > 0 and len(normal_amount_df) > 0:
            high_amount = high_amount_df['fraud_score'].mean()
            normal_amount = normal_amount_df['fraud_score'].mean()
            self.assertGreater(high_amount, normal_amount)
        else:
            # Se não houver dados suficientes, apenas verificar que scores existem
            self.assertTrue((df['fraud_score'] >= 0).all())

    def test_timestamp_ordering(self):
        """Testa que timestamps estão ordenados"""
        df = self.generator.generate_transaction_features(50)
        
        # DataFrame deve estar ordenado por timestamp
        timestamps = pd.to_datetime(df['timestamp'])
        self.assertTrue(timestamps.is_monotonic_increasing)


if __name__ == '__main__':
    unittest.main(verbosity=2)
