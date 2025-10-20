#!/usr/bin/env python3
"""
Exemplo de Uso da API REST
Author: Gabriel Demetrios Lafis
Year: 2025

Este exemplo demonstra como usar a API REST da Feature Store.
NOTA: Execute 'python src/feature_serving_api.py' em outro terminal primeiro!
"""

import sys
import os
import requests
import json
import time

# Configuração da API
API_BASE_URL = "http://localhost:5000"


def print_section(title):
    """Helper para imprimir seções"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def check_api_health():
    """Verifica se a API está respondendo"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print("✅ API está online e saudável")
            print(f"   Service: {data.get('service')}")
            print(f"   Status: {data.get('status')}")
            return True
        else:
            print("❌ API respondeu mas com erro")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar à API")
        print("\n💡 Inicie o servidor da API em outro terminal:")
        print("   python src/feature_serving_api.py\n")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar health: {e}")
        return False


def main():
    print_section("EXEMPLO DE USO DA API REST")
    
    print("1️⃣  Verificando conexão com a API...")
    if not check_api_health():
        sys.exit(1)
    
    # 2. Listar feature groups
    print("\n2️⃣  Listando feature groups disponíveis...")
    response = requests.get(f"{API_BASE_URL}/groups")
    if response.status_code == 200:
        data = response.json()
        groups = data.get("groups", [])
        print(f"   ✓ Encontrados {len(groups)} feature groups:")
        for group in groups:
            print(f"      • {group['name']} ({group['entity']})")
            print(f"        Descrição: {group['description']}")
            print(f"        Features: {group['num_features']}")
    else:
        print("   ⚠️  Nenhum feature group registrado ainda")
    
    # 3. Ingerir features
    print("\n3️⃣  Ingerindo features de exemplo...")
    
    customers_to_ingest = [
        {
            "entity_id": "CUST_API_001",
            "data": {
                "total_purchases": 20,
                "total_spent": 2500.00,
                "customer_segment": "gold"
            }
        },
        {
            "entity_id": "CUST_API_002",
            "data": {
                "total_purchases": 8,
                "total_spent": 800.00,
                "customer_segment": "silver"
            }
        }
    ]
    
    # Primeiro, vamos criar um feature group via código Python
    # (a API não tem endpoint de criação de grupos neste exemplo)
    print("   Nota: Criando feature group via código Python...")
    
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from feature_store import (
        FeatureStore,
        FeatureGroup,
        FeatureMetadata,
        FeatureType,
        FeatureStatus
    )
    
    fs = FeatureStore(
        name="api-example-fs",
        redis_host="localhost",
        redis_port=6379
    )
    
    customer_fg = FeatureGroup(
        name="customer_api_demo",
        entity="customer",
        description="Features para demonstração da API",
        features=[
            FeatureMetadata(
                name="total_purchases",
                description="Total de compras",
                feature_type=FeatureType.NUMERICAL,
                entity="customer",
                owner="api-demo@example.com",
                status=FeatureStatus.ACTIVE
            ),
            FeatureMetadata(
                name="total_spent",
                description="Total gasto",
                feature_type=FeatureType.NUMERICAL,
                entity="customer",
                owner="api-demo@example.com",
                status=FeatureStatus.ACTIVE
            ),
            FeatureMetadata(
                name="customer_segment",
                description="Segmento do cliente",
                feature_type=FeatureType.CATEGORICAL,
                entity="customer",
                owner="api-demo@example.com",
                status=FeatureStatus.ACTIVE
            )
        ]
    )
    
    fs.register_feature_group(customer_fg)
    print("   ✓ Feature group 'customer_api_demo' criado")
    
    # Agora ingerir via API
    print("\n   Ingerindo dados via API POST...")
    for customer in customers_to_ingest:
        response = requests.post(
            f"{API_BASE_URL}/ingest/customer_api_demo/{customer['entity_id']}",
            json=customer['data'],
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            print(f"   ✓ Features ingeridas para {customer['entity_id']}")
        else:
            print(f"   ❌ Erro ao ingerir {customer['entity_id']}: {response.text}")
    
    # Pequeno delay para garantir que os dados foram gravados
    time.sleep(0.5)
    
    # 4. Buscar features via API
    print("\n4️⃣  Buscando features via API GET...")
    
    for customer in customers_to_ingest:
        entity_id = customer['entity_id']
        response = requests.get(
            f"{API_BASE_URL}/features/customer_api_demo/{entity_id}"
        )
        
        if response.status_code == 200:
            features = response.json()
            print(f"\n   📊 Features de {entity_id}:")
            print(f"      Total de compras: {features.get('total_purchases')}")
            print(f"      Total gasto: R$ {features.get('total_spent')}")
            print(f"      Segmento: {features.get('customer_segment')}")
        else:
            print(f"   ❌ Erro ao buscar features de {entity_id}")
    
    # 5. Buscar features específicas (com filtro)
    print("\n5️⃣  Buscando apenas features específicas...")
    
    entity_id = "CUST_API_001"
    features_filter = "total_purchases,customer_segment"
    response = requests.get(
        f"{API_BASE_URL}/features/customer_api_demo/{entity_id}?features={features_filter}"
    )
    
    if response.status_code == 200:
        features = response.json()
        print(f"\n   📊 Features filtradas de {entity_id}:")
        for key, value in features.items():
            print(f"      {key}: {value}")
    
    # 6. Listar todas as features
    print("\n6️⃣  Listando todas as features registradas...")
    response = requests.get(f"{API_BASE_URL}/features")
    
    if response.status_code == 200:
        data = response.json()
        features_list = data.get("features", [])
        print(f"\n   Total: {len(features_list)} features")
        for feature in features_list:
            print(f"\n   • {feature['name']}")
            print(f"     Tipo: {feature['type']}")
            print(f"     Descrição: {feature['description']}")
            print(f"     Status: {feature['status']}")
    
    # 7. Buscar metadados de feature específica
    print("\n7️⃣  Buscando metadados de feature específica...")
    response = requests.get(
        f"{API_BASE_URL}/features/customer/total_purchases/metadata"
    )
    
    if response.status_code == 200:
        metadata = response.json()
        print(f"\n   📋 Metadados de 'total_purchases':")
        print(f"      Nome: {metadata.get('name')}")
        print(f"      Tipo: {metadata.get('type')}")
        print(f"      Descrição: {metadata.get('description')}")
        print(f"      Owner: {metadata.get('owner')}")
        print(f"      Tags: {', '.join(metadata.get('tags', []))}")
        print(f"      Status: {metadata.get('status')}")
        print(f"      Versão: {metadata.get('version')}")
    
    # 8. Exemplo de uso em produção (simulação)
    print("\n8️⃣  Simulando uso em produção (inferência em tempo real)...")
    print("\n   Cenário: Sistema de recomendação precisa das features de um cliente")
    
    customer_id_for_inference = "CUST_API_001"
    
    # Simular chamada do modelo de ML
    print(f"\n   🤖 Modelo solicitando features de {customer_id_for_inference}...")
    
    start_time = time.time()
    response = requests.get(
        f"{API_BASE_URL}/features/customer_api_demo/{customer_id_for_inference}"
    )
    latency = (time.time() - start_time) * 1000  # em ms
    
    if response.status_code == 200:
        features = response.json()
        print(f"   ✓ Features recebidas em {latency:.2f}ms")
        print(f"   📊 Usando features para inferência:")
        print(f"      {features}")
        print(f"\n   🎯 Modelo retorna: Recomendação personalizada gerada!")
    
    print_section("✅ EXEMPLO CONCLUÍDO COM SUCESSO")
    
    print("💡 Resumo do que foi demonstrado:")
    print("   ✅ Health check da API")
    print("   ✅ Listagem de feature groups")
    print("   ✅ Ingestão de features via POST")
    print("   ✅ Busca de features via GET")
    print("   ✅ Filtro de features específicas")
    print("   ✅ Listagem de todas as features")
    print("   ✅ Busca de metadados de features")
    print("   ✅ Simulação de uso em produção\n")
    
    print("📚 Próximos passos:")
    print("   • Explore outros endpoints da API")
    print("   • Integre com seu pipeline de ML")
    print("   • Configure monitoramento e alertas")
    print("   • Veja a documentação completa em docs/\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
