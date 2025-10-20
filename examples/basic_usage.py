#!/usr/bin/env python3
"""
Exemplo Básico de Uso da Feature Store
Author: Gabriel Demetrios Lafis
Year: 2025

Este exemplo demonstra o uso básico da Feature Store:
- Inicialização
- Criação de feature groups
- Ingestão de dados
- Busca de features online
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from feature_store import (
    FeatureStore,
    FeatureGroup,
    FeatureMetadata,
    FeatureType,
    FeatureStatus
)
from datetime import datetime


def main():
    print("\n" + "="*70)
    print("EXEMPLO BÁSICO - Feature Store")
    print("="*70 + "\n")
    
    # 1. Inicializar Feature Store
    print("1️⃣  Inicializando Feature Store...")
    fs = FeatureStore(
        name="basic-example-fs",
        redis_host="localhost",
        redis_port=6379,
        offline_store_path="./data/examples/basic_offline"
    )
    print("   ✓ Feature Store inicializada\n")
    
    # 2. Criar Feature Group
    print("2️⃣  Criando Feature Group 'customer_metrics'...")
    customer_fg = FeatureGroup(
        name="customer_metrics",
        entity="customer",
        description="Métricas básicas de clientes",
        features=[
            FeatureMetadata(
                name="total_purchases",
                description="Número total de compras realizadas",
                feature_type=FeatureType.NUMERICAL,
                entity="customer",
                owner="analytics@example.com",
                tags=["customer", "purchases", "behavior"],
                status=FeatureStatus.ACTIVE
            ),
            FeatureMetadata(
                name="total_spent",
                description="Valor total gasto pelo cliente",
                feature_type=FeatureType.NUMERICAL,
                entity="customer",
                owner="analytics@example.com",
                tags=["customer", "revenue", "behavior"],
                status=FeatureStatus.ACTIVE
            ),
            FeatureMetadata(
                name="customer_segment",
                description="Segmento do cliente (bronze, silver, gold, platinum)",
                feature_type=FeatureType.CATEGORICAL,
                entity="customer",
                owner="marketing@example.com",
                tags=["customer", "segment", "marketing"],
                status=FeatureStatus.ACTIVE
            )
        ]
    )
    
    fs.register_feature_group(customer_fg)
    print("   ✓ Feature Group registrado\n")
    
    # 3. Ingerir dados de exemplo
    print("3️⃣  Ingerindo dados de clientes...")
    
    customers_data = [
        {
            "entity_id": "CUST001",
            "data": {
                "total_purchases": 15,
                "total_spent": 1500.00,
                "customer_segment": "gold"
            }
        },
        {
            "entity_id": "CUST002",
            "data": {
                "total_purchases": 5,
                "total_spent": 250.00,
                "customer_segment": "bronze"
            }
        },
        {
            "entity_id": "CUST003",
            "data": {
                "total_purchases": 30,
                "total_spent": 4500.00,
                "customer_segment": "platinum"
            }
        }
    ]
    
    for customer in customers_data:
        fs.ingest_features(
            "customer_metrics",
            customer["entity_id"],
            customer["data"]
        )
        print(f"   ✓ Dados ingeridos para {customer['entity_id']}")
    
    print()
    
    # 4. Buscar features online
    print("4️⃣  Buscando features online...")
    for customer in customers_data:
        entity_id = customer["entity_id"]
        features = fs.get_online_features("customer_metrics", entity_id)
        print(f"\n   📊 Features de {entity_id}:")
        for key, value in features.items():
            if key not in ["entity_id", "timestamp", "date"]:
                print(f"      • {key}: {value}")
    
    print()
    
    # 5. Listar todas as features registradas
    print("5️⃣  Listando todas as features registradas...")
    all_features = fs.list_features()
    print(f"\n   Total: {len(all_features)} features")
    for feature in all_features:
        print(f"   • {feature.name}")
        print(f"     Tipo: {feature.feature_type.value}")
        print(f"     Descrição: {feature.description}")
        print(f"     Owner: {feature.owner}")
        print()
    
    # 6. Buscar features offline (histórico)
    print("6️⃣  Buscando features offline (para treinamento)...")
    offline_features = fs.get_offline_features("customer_metrics")
    if offline_features is not None and not offline_features.empty:
        print(f"\n   ✓ {len(offline_features)} registros encontrados")
        print("\n   Exemplo de dados offline:")
        print(offline_features[["entity_id", "total_purchases", "total_spent", "customer_segment"]].head())
    else:
        print("   ⚠ Nenhum dado offline encontrado")
    
    print("\n" + "="*70)
    print("✅ Exemplo concluído com sucesso!")
    print("="*70 + "\n")
    
    print("💡 Próximos passos:")
    print("   • Execute 'python examples/advanced_transformations.py' para ver transformações")
    print("   • Execute 'python src/feature_serving_api.py' para iniciar a API")
    print("   • Consulte a documentação em docs/ para mais detalhes\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\n💡 Certifique-se de que o Redis está rodando:")
        print("   docker run --name feature-store-redis -p 6379:6379 -d redis/redis-stack-server:latest\n")
        sys.exit(1)
