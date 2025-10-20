# Feature Store Quick Reference

Guia rápido de referência para comandos e APIs mais utilizados.

## 🚀 Setup Rápido

```bash
# Clone e instale
git clone https://github.com/galafis/feature-store-architecture.git
cd feature-store-architecture
pip install -r requirements.txt

# Inicie Redis
docker run -d -p 6379:6379 --name feature-store-redis redis/redis-stack-server:latest

# Execute exemplo
python examples/basic_usage.py
```

## 📦 Imports Principais

```python
from src.feature_store import (
    FeatureStore,
    FeatureGroup,
    FeatureMetadata,
    FeatureType,
    FeatureStatus,
    FeatureTransformation,
    FeatureValidation
)
```

## 🏗️ Inicialização

```python
# Feature Store básica
fs = FeatureStore(name="my-fs")

# Com configurações
fs = FeatureStore(
    name="production-fs",
    redis_host="localhost",
    redis_port=6379,
    offline_store_path="./data/offline"
)
```

## 🎯 Criar Features

### Feature Simples

```python
feature = FeatureMetadata(
    name="total_purchases",
    description="Número total de compras",
    feature_type=FeatureType.NUMERICAL,
    entity="customer",
    owner="team@company.com",
    status=FeatureStatus.ACTIVE,
    tags=["customer", "purchases"]
)
```

### Feature com Transformação

```python
feature = FeatureMetadata(
    name="avg_order_value",
    description="Valor médio por pedido",
    feature_type=FeatureType.NUMERICAL,
    entity="customer",
    owner="team@company.com",
    transformation=FeatureTransformation(
        name="calc_avg",
        description="Calcula média",
        source_features=["total_spent", "total_orders"],
        transformation_fn=lambda d: d["total_spent"] / d["total_orders"]
    )
)
```

### Feature com Validação

```python
feature = FeatureMetadata(
    name="customer_age",
    description="Idade do cliente",
    feature_type=FeatureType.NUMERICAL,
    entity="customer",
    owner="team@company.com",
    validation=FeatureValidation(
        min_value=18,
        max_value=120,
        not_null=True
    )
)
```

## 📊 Feature Groups

```python
# Criar Feature Group
fg = FeatureGroup(
    name="customer_features",
    entity="customer",
    description="Features de clientes",
    features=[feature1, feature2, feature3]  # Lista de FeatureMetadata
)

# Registrar
fs.register_feature_group(fg)
```

## 💾 Ingestão de Dados

```python
# Ingerir features
fs.ingest_features(
    "customer_features",
    "CUST001",
    {
        "total_purchases": 10,
        "total_spent": 1000.00
    }
)
```

## 🔍 Buscar Features

### Online (Redis) - Baixa Latência

```python
# Buscar features online
features = fs.get_online_features("customer_features", "CUST001")
# Retorna: {"total_purchases": "10", "total_spent": "1000.00", ...}
```

### Offline (Parquet) - Para Treinamento

```python
from datetime import datetime, timedelta

# Buscar features históricas
df = fs.get_historical_features(
    "customer_features",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31)
)

# Ou buscar todos os dados
df = fs.get_offline_features("customer_features")
```

## 📋 Listar e Descobrir

```python
# Listar todas as features
all_features = fs.list_features()
for feature in all_features:
    print(f"{feature.name}: {feature.description}")

# Buscar metadados de feature específica
metadata = fs.get_feature_metadata("total_purchases", "customer")
```

## 🔄 Gerenciar Lifecycle

```python
# Depreciar feature
fs.deprecate_feature("old_feature_name", "customer")

# Verificar status
metadata = fs.get_feature_metadata("old_feature_name", "customer")
print(metadata.status)  # FeatureStatus.DEPRECATED
```

## 🌐 API REST

### Iniciar Servidor

```python
from src.feature_serving_api import create_app

app = create_app()
app.run(host='0.0.0.0', port=5000)
```

### Endpoints

```bash
# Health check
curl http://localhost:5000/health

# Listar groups
curl http://localhost:5000/groups

# Listar features
curl http://localhost:5000/features

# Buscar features
curl http://localhost:5000/features/customer_features/CUST001

# Buscar features específicas
curl "http://localhost:5000/features/customer_features/CUST001?features=total_purchases,avg_order_value"

# Ingerir features
curl -X POST http://localhost:5000/ingest/customer_features/CUST001 \
  -H "Content-Type: application/json" \
  -d '{"total_purchases": 15, "total_spent": 1500.00}'

# Buscar metadados
curl http://localhost:5000/features/customer/total_purchases/metadata
```

## 🧪 Testes

```bash
# Todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=src --cov-report=html

# Teste específico
pytest tests/test_feature_store.py::TestFeatureStore::test_ingest_data_online_store -v
```

## 📊 Tipos de Features

```python
FeatureType.NUMERICAL      # Valores numéricos
FeatureType.CATEGORICAL    # Categorias
FeatureType.BOOLEAN        # Verdadeiro/Falso
FeatureType.TIMESTAMP      # Data/hora
FeatureType.TEXT           # Texto livre
FeatureType.EMBEDDING      # Vetores de embedding
```

## 🏷️ Status de Features

```python
FeatureStatus.DRAFT        # Em desenvolvimento
FeatureStatus.ACTIVE       # Em produção
FeatureStatus.DEPRECATED   # Marcada para remoção
FeatureStatus.ARCHIVED     # Arquivada (histórico)
```

## ⚡ Comandos Redis Úteis

```bash
# Conectar ao Redis
redis-cli

# Ver todas as chaves
KEYS *

# Ver feature específica
HGETALL customer_features:CUST001

# Limpar banco (cuidado!)
FLUSHDB

# Ver info de memória
INFO memory

# Monitorar comandos
MONITOR
```

## 🐛 Troubleshooting Rápido

### Redis Connection Error
```bash
# Verificar se está rodando
redis-cli ping

# Reiniciar Docker
docker restart feature-store-redis

# Ver logs
docker logs feature-store-redis
```

### Import Error
```bash
# Reinstalar dependências
pip install -r requirements.txt
```

### Parquet Error
```python
# Verificar se diretório existe
import os
os.makedirs("./data/offline_store", exist_ok=True)
```

## 📚 Links Úteis

- **Docs Completos**: [docs/](.)
- **Getting Started**: [GETTING_STARTED.md](GETTING_STARTED.md)
- **Arquitetura**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Best Practices**: [BEST_PRACTICES.md](BEST_PRACTICES.md)
- **Exemplos**: [../examples/](../examples/)
- **Testes**: [../tests/](../tests/)

## 💡 Exemplos Rápidos

### Exemplo Completo Mínimo

```python
from src.feature_store import *

# 1. Criar
fs = FeatureStore(name="quick-fs")

# 2. Definir
fg = FeatureGroup(
    name="users",
    entity="user",
    description="User features",
    features=[
        FeatureMetadata(
            name="score",
            description="User score",
            feature_type=FeatureType.NUMERICAL,
            entity="user",
            owner="me@example.com",
            status=FeatureStatus.ACTIVE
        )
    ]
)

# 3. Registrar
fs.register_feature_group(fg)

# 4. Ingerir
fs.ingest_features("users", "USER001", {"score": 95})

# 5. Buscar
features = fs.get_online_features("users", "USER001")
print(features)  # {"score": "95", ...}
```

### Pipeline de ML Simples

```python
# Treinamento
df = fs.get_offline_features("customer_features")
X = df[["total_purchases", "avg_order_value"]]
y = df["churn"]
model.fit(X, y)

# Inferência
features = fs.get_online_features("customer_features", customer_id)
prediction = model.predict([[
    float(features["total_purchases"]),
    float(features["avg_order_value"])
]])
```

## 🔐 Variáveis de Ambiente

```bash
# .env file
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
OFFLINE_STORE_PATH=./data/offline_store
API_PORT=5000
```

```python
# Uso no código
import os
from dotenv import load_dotenv

load_dotenv()

fs = FeatureStore(
    name="my-fs",
    redis_host=os.getenv("REDIS_HOST", "localhost"),
    redis_port=int(os.getenv("REDIS_PORT", 6379)),
    offline_store_path=os.getenv("OFFLINE_STORE_PATH", "./data/offline")
)
```

---

**Dica**: Mantenha esta página aberta enquanto desenvolve! 🚀
