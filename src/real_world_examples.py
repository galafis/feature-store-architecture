"""
Feature Store Architecture - Real World Examples
Author: Gabriel Demetrios Lafis
Year: 2025

Este módulo demonstra casos de uso reais da Feature Store com dados de exemplo
baseados em cenários comuns de ML (e-commerce, finanças, recomendação).
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import os


class EcommerceFeatureGenerator:
    """
    Gerador de features para um sistema de e-commerce.
    Simula features comuns usadas em sistemas de recomendação e previsão de churn.
    """
    
    @staticmethod
    def generate_customer_features(num_customers: int = 1000) -> pd.DataFrame:
        """
        Gera features de clientes para um sistema de e-commerce.
        
        Args:
            num_customers: Número de clientes a gerar
            
        Returns:
            DataFrame com features de clientes
        """
        np.random.seed(42)
        
        # Gerar IDs de clientes
        customer_ids = [f"CUST_{i:06d}" for i in range(num_customers)]
        
        # Features demográficas
        ages = np.random.normal(35, 12, num_customers).astype(int)
        ages = np.clip(ages, 18, 80)
        
        genders = np.random.choice(['M', 'F', 'Other'], num_customers, p=[0.48, 0.48, 0.04])
        
        # Features comportamentais
        total_purchases = np.random.poisson(15, num_customers)
        total_spent = np.random.gamma(2, 500, num_customers)
        avg_order_value = total_spent / np.maximum(total_purchases, 1)
        
        # Features de engajamento
        days_since_last_purchase = np.random.exponential(30, num_customers).astype(int)
        days_since_last_purchase = np.clip(days_since_last_purchase, 0, 365)
        
        email_open_rate = np.random.beta(2, 5, num_customers)
        app_sessions_per_week = np.random.poisson(5, num_customers)
        
        # Features de preferência
        favorite_categories = np.random.choice(
            ['Electronics', 'Fashion', 'Home', 'Sports', 'Books'],
            num_customers
        )
        
        # Features de risco
        churn_probability = 1 / (1 + np.exp(-(days_since_last_purchase - 60) / 20))
        
        # Features temporais
        customer_tenure_days = np.random.randint(30, 1825, num_customers)
        
        # Criar DataFrame
        df = pd.DataFrame({
            'customer_id': customer_ids,
            'age': ages,
            'gender': genders,
            'total_purchases': total_purchases,
            'total_spent': total_spent.round(2),
            'avg_order_value': avg_order_value.round(2),
            'days_since_last_purchase': days_since_last_purchase,
            'email_open_rate': email_open_rate.round(3),
            'app_sessions_per_week': app_sessions_per_week,
            'favorite_category': favorite_categories,
            'churn_probability': churn_probability.round(3),
            'customer_tenure_days': customer_tenure_days,
            'timestamp': datetime.now()
        })
        
        return df
    
    @staticmethod
    def generate_product_features(num_products: int = 500) -> pd.DataFrame:
        """
        Gera features de produtos para um sistema de e-commerce.
        
        Args:
            num_products: Número de produtos a gerar
            
        Returns:
            DataFrame com features de produtos
        """
        np.random.seed(43)
        
        # Gerar IDs de produtos
        product_ids = [f"PROD_{i:06d}" for i in range(num_products)]
        
        # Features de produto
        categories = np.random.choice(
            ['Electronics', 'Fashion', 'Home', 'Sports', 'Books'],
            num_products
        )
        
        prices = np.random.gamma(3, 50, num_products)
        prices = np.clip(prices, 10, 5000).round(2)
        
        # Features de popularidade
        view_count = np.random.poisson(100, num_products)
        purchase_count = (view_count * np.random.beta(2, 10, num_products)).astype(int)
        conversion_rate = purchase_count / np.maximum(view_count, 1)
        
        # Features de qualidade
        avg_rating = np.random.beta(8, 2, num_products) * 4 + 1  # Entre 1 e 5
        num_reviews = np.random.poisson(20, num_products)
        
        # Features de estoque
        stock_quantity = np.random.poisson(50, num_products)
        days_in_stock = np.random.randint(1, 365, num_products)
        
        # Features de desconto
        discount_percentage = np.random.choice(
            [0, 5, 10, 15, 20, 25, 30],
            num_products,
            p=[0.4, 0.15, 0.15, 0.1, 0.1, 0.05, 0.05]
        )
        
        # Criar DataFrame
        df = pd.DataFrame({
            'product_id': product_ids,
            'category': categories,
            'price': prices,
            'view_count': view_count,
            'purchase_count': purchase_count,
            'conversion_rate': conversion_rate.round(3),
            'avg_rating': avg_rating.round(2),
            'num_reviews': num_reviews,
            'stock_quantity': stock_quantity,
            'days_in_stock': days_in_stock,
            'discount_percentage': discount_percentage,
            'timestamp': datetime.now()
        })
        
        return df
    
    @staticmethod
    def generate_interaction_features(
        customer_df: pd.DataFrame,
        product_df: pd.DataFrame,
        num_interactions: int = 5000
    ) -> pd.DataFrame:
        """
        Gera features de interação cliente-produto.
        
        Args:
            customer_df: DataFrame de clientes
            product_df: DataFrame de produtos
            num_interactions: Número de interações a gerar
            
        Returns:
            DataFrame com features de interação
        """
        np.random.seed(44)
        
        # Selecionar clientes e produtos aleatórios
        customer_ids = np.random.choice(customer_df['customer_id'], num_interactions)
        product_ids = np.random.choice(product_df['product_id'], num_interactions)
        
        # Tipos de interação
        interaction_types = np.random.choice(
            ['view', 'add_to_cart', 'purchase', 'wishlist'],
            num_interactions,
            p=[0.6, 0.2, 0.15, 0.05]
        )
        
        # Timestamps de interação (últimos 30 dias)
        timestamps = [
            datetime.now() - timedelta(days=np.random.randint(0, 30))
            for _ in range(num_interactions)
        ]
        
        # Features contextuais
        devices = np.random.choice(['mobile', 'desktop', 'tablet'], num_interactions, p=[0.6, 0.3, 0.1])
        session_durations = np.random.exponential(300, num_interactions).astype(int)  # segundos
        
        # Criar DataFrame
        df = pd.DataFrame({
            'interaction_id': [f"INT_{i:08d}" for i in range(num_interactions)],
            'customer_id': customer_ids,
            'product_id': product_ids,
            'interaction_type': interaction_types,
            'device': devices,
            'session_duration_seconds': session_durations,
            'timestamp': timestamps
        })
        
        return df.sort_values('timestamp')


class FinancialFeatureGenerator:
    """
    Gerador de features para aplicações financeiras.
    Simula features usadas em detecção de fraude e credit scoring.
    """
    
    @staticmethod
    def generate_transaction_features(num_transactions: int = 2000) -> pd.DataFrame:
        """
        Gera features de transações financeiras.
        
        Args:
            num_transactions: Número de transações a gerar
            
        Returns:
            DataFrame com features de transações
        """
        np.random.seed(45)
        
        # IDs
        transaction_ids = [f"TXN_{i:08d}" for i in range(num_transactions)]
        account_ids = [f"ACC_{i:06d}" for i in np.random.randint(0, 500, num_transactions)]
        
        # Valores de transação
        amounts = np.random.gamma(2, 100, num_transactions)
        amounts = np.clip(amounts, 1, 10000).round(2)
        
        # Tipos de transação
        transaction_types = np.random.choice(
            ['purchase', 'withdrawal', 'transfer', 'payment'],
            num_transactions,
            p=[0.5, 0.2, 0.2, 0.1]
        )
        
        # Localização
        countries = np.random.choice(
            ['BR', 'US', 'UK', 'DE', 'FR', 'JP', 'CN'],
            num_transactions,
            p=[0.5, 0.15, 0.1, 0.08, 0.07, 0.05, 0.05]
        )
        
        # Features temporais
        timestamps = [
            datetime.now() - timedelta(days=np.random.randint(0, 90))
            for _ in range(num_transactions)
        ]
        hours = [ts.hour for ts in timestamps]
        
        # Features de risco
        is_international = (countries != 'BR').astype(int)
        is_high_amount = (amounts > 1000).astype(int)
        is_unusual_hour = ((np.array(hours) < 6) | (np.array(hours) > 22)).astype(int)
        
        fraud_score = (
            is_international * 0.3 +
            is_high_amount * 0.4 +
            is_unusual_hour * 0.3 +
            np.random.normal(0, 0.1, num_transactions)
        )
        fraud_score = np.clip(fraud_score, 0, 1).round(3)
        
        # Criar DataFrame
        df = pd.DataFrame({
            'transaction_id': transaction_ids,
            'account_id': account_ids,
            'amount': amounts,
            'transaction_type': transaction_types,
            'country': countries,
            'hour_of_day': hours,
            'is_international': is_international,
            'is_high_amount': is_high_amount,
            'is_unusual_hour': is_unusual_hour,
            'fraud_score': fraud_score,
            'timestamp': timestamps
        })
        
        return df.sort_values('timestamp')


def demonstrate_feature_engineering():
    """
    Demonstra engenharia de features com dados reais simulados.
    """
    print("\n" + "=" * 80)
    print("Feature Store - Real World Examples")
    print("Demonstrando geração de features para cenários reais")
    print("=" * 80)
    
    # Exemplo 1: E-commerce
    print("\n" + "-" * 40)
    print("Exemplo 1: Features de E-commerce")
    print("-" * 40)
    
    ecommerce_gen = EcommerceFeatureGenerator()
    
    customers_df = ecommerce_gen.generate_customer_features(100)
    print(f"\n✓ Geradas {len(customers_df)} features de clientes")
    print("\nPrimeiras 5 linhas:")
    print(customers_df.head())
    
    print("\nEstatísticas das features:")
    print(customers_df[['age', 'total_spent', 'churn_probability']].describe())
    
    products_df = ecommerce_gen.generate_product_features(50)
    print(f"\n✓ Geradas {len(products_df)} features de produtos")
    print("\nPrimeiras 5 linhas:")
    print(products_df.head())
    
    interactions_df = ecommerce_gen.generate_interaction_features(customers_df, products_df, 500)
    print(f"\n✓ Geradas {len(interactions_df)} features de interações")
    print("\nDistribuição de tipos de interação:")
    print(interactions_df['interaction_type'].value_counts())
    
    # Exemplo 2: Finanças
    print("\n" + "-" * 40)
    print("Exemplo 2: Features Financeiras")
    print("-" * 40)
    
    financial_gen = FinancialFeatureGenerator()
    
    transactions_df = financial_gen.generate_transaction_features(200)
    print(f"\n✓ Geradas {len(transactions_df)} features de transações")
    print("\nPrimeiras 5 linhas:")
    print(transactions_df.head())
    
    print("\nDistribuição de scores de fraude:")
    print(transactions_df['fraud_score'].describe())
    
    print("\nTransações de alto risco (fraud_score > 0.7):")
    high_risk = transactions_df[transactions_df['fraud_score'] > 0.7]
    print(f"Total: {len(high_risk)} transações ({len(high_risk)/len(transactions_df)*100:.1f}%)")
    
    # Salvar datasets de exemplo
    print("\n" + "-" * 40)
    print("Salvando datasets de exemplo")
    print("-" * 40)
    
    output_dir = "../data/examples"
    os.makedirs(output_dir, exist_ok=True)
    
    customers_df.to_parquet(f"{output_dir}/ecommerce_customers.parquet", index=False)
    products_df.to_parquet(f"{output_dir}/ecommerce_products.parquet", index=False)
    interactions_df.to_parquet(f"{output_dir}/ecommerce_interactions.parquet", index=False)
    transactions_df.to_parquet(f"{output_dir}/financial_transactions.parquet", index=False)
    
    print(f"✓ Datasets salvos em {output_dir}/")
    print("  - ecommerce_customers.parquet")
    print("  - ecommerce_products.parquet")
    print("  - ecommerce_interactions.parquet")
    print("  - financial_transactions.parquet")


if __name__ == "__main__":
    demonstrate_feature_engineering()
