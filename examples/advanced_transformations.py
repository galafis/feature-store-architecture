#!/usr/bin/env python3
"""
Exemplo Avançado - Transformações de Features
Author: Gabriel Demetrios Lafis
Year: 2025

Este exemplo demonstra:
- Transformações complexas de features
- Validações avançadas
- Features derivadas de outras features
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from feature_store import (
    FeatureStore,
    FeatureGroup,
    FeatureMetadata,
    FeatureType,
    FeatureStatus,
    FeatureTransformation,
    FeatureValidation
)
from datetime import datetime, timedelta


def calculate_recency_score(data):
    """Calcula score de recência baseado em dias desde última compra"""
    days = data.get("days_since_last_purchase", 365)
    # Score entre 0 e 1, onde 1 = comprou hoje, 0 = muito tempo sem comprar
    return round(1 / (1 + days / 30), 3)


def calculate_clv_prediction(data):
    """Predição simples de Customer Lifetime Value"""
    avg_value = data.get("avg_order_value", 0)
    frequency = data.get("purchase_frequency", 0)
    tenure = data.get("customer_tenure_days", 30)
    
    # Fórmula simplificada: valor médio * frequência * (tenure em meses)
    clv = avg_value * frequency * (tenure / 30)
    return round(clv, 2)


def main():
    print("\n" + "="*70)
    print("EXEMPLO AVANÇADO - Transformações de Features")
    print("="*70 + "\n")
    
    # Inicializar Feature Store
    print("1️⃣  Inicializando Feature Store...")
    fs = FeatureStore(
        name="advanced-example-fs",
        redis_host="localhost",
        redis_port=6379,
        offline_store_path="./data/examples/advanced_offline"
    )
    print("   ✓ Feature Store inicializada\n")
    
    # Criar Feature Group com transformações
    print("2️⃣  Criando Feature Group com transformações avançadas...")
    
    customer_advanced_fg = FeatureGroup(
        name="customer_advanced",
        entity="customer",
        description="Features avançadas com transformações",
        features=[
            # Feature simples (armazenada diretamente)
            FeatureMetadata(
                name="total_purchases",
                description="Total de compras",
                feature_type=FeatureType.NUMERICAL,
                entity="customer",
                owner="analytics@example.com",
                validation=FeatureValidation(min_value=0, not_null=True)
            ),
            
            FeatureMetadata(
                name="total_spent",
                description="Total gasto",
                feature_type=FeatureType.NUMERICAL,
                entity="customer",
                owner="analytics@example.com",
                validation=FeatureValidation(min_value=0, not_null=True)
            ),
            
            # Feature transformada: valor médio por pedido
            FeatureMetadata(
                name="avg_order_value",
                description="Valor médio por pedido (transformação)",
                feature_type=FeatureType.NUMERICAL,
                entity="customer",
                owner="analytics@example.com",
                transformation=FeatureTransformation(
                    name="calculate_avg_order",
                    description="Calcula valor médio dos pedidos",
                    source_features=["total_spent", "total_purchases"],
                    transformation_fn=lambda data: round(
                        data["total_spent"] / data["total_purchases"]
                        if data["total_purchases"] > 0 else 0,
                        2
                    )
                ),
                validation=FeatureValidation(min_value=0)
            ),
            
            # Feature transformada: score de recência
            FeatureMetadata(
                name="recency_score",
                description="Score de recência do cliente (0-1)",
                feature_type=FeatureType.NUMERICAL,
                entity="customer",
                owner="analytics@example.com",
                transformation=FeatureTransformation(
                    name="calculate_recency",
                    description="Calcula score baseado em última compra",
                    source_features=["days_since_last_purchase"],
                    transformation_fn=calculate_recency_score
                ),
                validation=FeatureValidation(min_value=0, max_value=1)
            ),
            
            # Feature simples para a transformação de CLV
            FeatureMetadata(
                name="days_since_last_purchase",
                description="Dias desde última compra",
                feature_type=FeatureType.NUMERICAL,
                entity="customer",
                owner="analytics@example.com",
                validation=FeatureValidation(min_value=0)
            ),
            
            FeatureMetadata(
                name="purchase_frequency",
                description="Frequência de compras (por mês)",
                feature_type=FeatureType.NUMERICAL,
                entity="customer",
                owner="analytics@example.com",
                validation=FeatureValidation(min_value=0)
            ),
            
            FeatureMetadata(
                name="customer_tenure_days",
                description="Tempo como cliente (dias)",
                feature_type=FeatureType.NUMERICAL,
                entity="customer",
                owner="analytics@example.com",
                validation=FeatureValidation(min_value=0)
            ),
            
            # Feature transformada complexa: predição de CLV
            FeatureMetadata(
                name="predicted_clv",
                description="Predição de Customer Lifetime Value",
                feature_type=FeatureType.NUMERICAL,
                entity="customer",
                owner="ml-team@example.com",
                transformation=FeatureTransformation(
                    name="predict_clv",
                    description="Prediz CLV baseado em comportamento histórico",
                    source_features=["avg_order_value", "purchase_frequency", "customer_tenure_days"],
                    transformation_fn=calculate_clv_prediction
                ),
                validation=FeatureValidation(min_value=0)
            )
        ]
    )
    
    fs.register_feature_group(customer_advanced_fg)
    print("   ✓ Feature Group registrado com 7 features (4 transformadas)\n")
    
    # Ingerir dados de exemplo
    print("3️⃣  Ingerindo dados de clientes...")
    
    customers_data = [
        {
            "entity_id": "CUST_ADV_001",
            "name": "Cliente Ativo",
            "data": {
                "total_purchases": 25,
                "total_spent": 3750.00,
                "days_since_last_purchase": 5,
                "purchase_frequency": 2.5,  # 2.5 compras/mês
                "customer_tenure_days": 300
            }
        },
        {
            "entity_id": "CUST_ADV_002",
            "name": "Cliente Em Risco",
            "data": {
                "total_purchases": 10,
                "total_spent": 1200.00,
                "days_since_last_purchase": 90,
                "purchase_frequency": 0.5,
                "customer_tenure_days": 600
            }
        },
        {
            "entity_id": "CUST_ADV_003",
            "name": "Cliente VIP",
            "data": {
                "total_purchases": 50,
                "total_spent": 12500.00,
                "days_since_last_purchase": 2,
                "purchase_frequency": 5.0,
                "customer_tenure_days": 365
            }
        }
    ]
    
    for customer in customers_data:
        fs.ingest_features(
            "customer_advanced",
            customer["entity_id"],
            customer["data"]
        )
        print(f"   ✓ Dados ingeridos para {customer['entity_id']} ({customer['name']})")
    
    print()
    
    # Buscar e exibir features transformadas
    print("4️⃣  Analisando features transformadas...")
    
    for customer in customers_data:
        entity_id = customer["entity_id"]
        name = customer["name"]
        features = fs.get_online_features("customer_advanced", entity_id)
        
        print(f"\n   📊 {name} ({entity_id}):")
        print(f"      📈 Features Brutas:")
        print(f"         • Total de compras: {features.get('total_purchases')}")
        print(f"         • Total gasto: R$ {features.get('total_spent')}")
        print(f"         • Dias desde última compra: {features.get('days_since_last_purchase')}")
        print(f"         • Frequência de compras: {features.get('purchase_frequency')} compras/mês")
        print(f"         • Tempo como cliente: {features.get('customer_tenure_days')} dias")
        
        print(f"\n      🔄 Features Transformadas:")
        print(f"         • Valor médio por pedido: R$ {features.get('avg_order_value')}")
        print(f"         • Score de recência: {features.get('recency_score')} (0-1)")
        print(f"         • CLV predito: R$ {features.get('predicted_clv')}")
        
        # Análise do perfil
        recency = float(features.get('recency_score', 0))
        clv = float(features.get('predicted_clv', 0))
        
        print(f"\n      💡 Análise:")
        if recency > 0.8:
            print(f"         ✅ Cliente muito ativo (compra frequentemente)")
        elif recency > 0.5:
            print(f"         ⚠️  Cliente moderadamente ativo")
        else:
            print(f"         🔴 Cliente em risco de churn (não compra há muito tempo)")
        
        if clv > 5000:
            print(f"         💎 Alto valor vitalício - cliente VIP")
        elif clv > 2000:
            print(f"         ⭐ Valor vitalício médio-alto")
        else:
            print(f"         📊 Valor vitalício moderado")
    
    print("\n" + "="*70)
    print("✅ Exemplo de transformações concluído!")
    print("="*70 + "\n")
    
    print("💡 Insights:")
    print("   • Features transformadas são calculadas automaticamente na ingestão")
    print("   • Validações garantem a qualidade dos dados")
    print("   • Mesma lógica é usada em treinamento e inferência")
    print("   • Features derivadas facilitam o trabalho dos modelos de ML\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Certifique-se de que o Redis está rodando:")
        print("   docker run --name feature-store-redis -p 6379:6379 -d redis/redis-stack-server:latest\n")
        sys.exit(1)
