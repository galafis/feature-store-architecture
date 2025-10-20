# Best Practices for Feature Store

Este documento descreve as melhores práticas para usar e manter uma Feature Store em produção.

## 📝 Nomenclatura de Features

### Convenções de Nome

**✅ Boas Práticas:**
```python
# Use nomes descritivos e específicos
"customer_total_purchases_30d"      # Bom
"customer_avg_order_value_90d"      # Bom
"product_view_count_7d"             # Bom

# Inclua a janela de tempo quando relevante
"user_clicks_last_7_days"
"transaction_amount_sum_30d"
```

**❌ Evite:**
```python
"feature1"                          # Muito genérico
"cust_feat"                        # Abreviações não claras
"x1"                               # Sem significado
"customerTotalPurchases"           # Use snake_case, não camelCase
```

### Padrões Recomendados

```
{entity}_{metric}_{aggregation}_{time_window}
```

Exemplos:
- `customer_purchases_count_30d`
- `product_revenue_sum_7d`
- `user_sessions_avg_24h`

## 🏷️ Organização com Tags

### Sistema de Tags Hierárquico

```python
tags = [
    "entity:customer",           # Entidade
    "domain:sales",             # Domínio de negócio
    "team:analytics",           # Time responsável
    "criticality:high",         # Criticidade
    "pii:false",               # Contém dados pessoais?
    "time_window:30d"          # Janela temporal
]
```

### Tags para Descoberta

```python
# Features de e-commerce
tags = ["ecommerce", "recommendation", "personalization"]

# Features de fraude
tags = ["fraud_detection", "risk", "real_time"]

# Features demográficas
tags = ["demographics", "customer_profile", "batch"]
```

## 🔄 Versionamento de Features

### Versionamento Semântico

Use versionamento semântico (MAJOR.MINOR.PATCH):

```python
# Versão 1.0.0 - Release inicial
FeatureMetadata(
    name="customer_ltv",
    version="1.0.0",
    # ...
)

# Versão 1.1.0 - Adição de nova lógica (compatível)
FeatureMetadata(
    name="customer_ltv",
    version="1.1.0",
    # ...
)

# Versão 2.0.0 - Mudança incompatível
FeatureMetadata(
    name="customer_ltv",
    version="2.0.0",
    # ...
)
```

### Deprecação Gradual

```python
# 1. Marcar como deprecated
fs.deprecate_feature("old_feature_name", "customer")

# 2. Documentar a feature de substituição
FeatureMetadata(
    name="old_feature_name",
    description="DEPRECATED: Use 'new_feature_name' instead",
    status=FeatureStatus.DEPRECATED
)

# 3. Manter por período de transição (ex: 3 meses)

# 4. Arquivar quando não houver mais uso
metadata.status = FeatureStatus.ARCHIVED
```

## ✅ Validação de Features

### Validações Essenciais

```python
# Features numéricas
FeatureValidation(
    min_value=0,
    max_value=1000000,
    not_null=True
)

# Features categóricas
FeatureValidation(
    allowed_values=["bronze", "silver", "gold", "platinum"],
    not_null=True
)

# Features de porcentagem
FeatureValidation(
    min_value=0.0,
    max_value=1.0,
    not_null=True
)
```

### Validação de Dados na Ingestão

```python
def validate_before_ingest(data: Dict) -> bool:
    # Validar tipos de dados
    if not isinstance(data.get("total_purchases"), (int, float)):
        return False
    
    # Validar valores de negócio
    if data.get("total_purchases", 0) < 0:
        return False
    
    # Validar completude
    required_fields = ["entity_id", "timestamp"]
    if not all(field in data for field in required_fields):
        return False
    
    return True
```

## 🎯 Transformações de Features

### Transformações Idempotentes

✅ **Boas Práticas:**
```python
# Transformação determinística
lambda data: data["total_spent"] / max(data["total_purchases"], 1)

# Sempre produz o mesmo resultado para os mesmos inputs
```

❌ **Evite:**
```python
# Transformação não-determinística
lambda data: data["value"] * random.random()  # ERRADO!

# Usa estado externo
lambda data: data["value"] + global_counter  # ERRADO!
```

### Transformações Documentadas

```python
FeatureTransformation(
    name="customer_recency_score",
    description="""
    Calcula score de recência do cliente baseado em última compra.
    
    Fórmula: 1 / (1 + days_since_last_purchase/30)
    
    Entrada:
        - last_purchase_date: Data da última compra
        - current_date: Data atual
    
    Saída:
        - float entre 0 e 1
        - 1 = comprou hoje
        - 0.5 = comprou há 30 dias
        - 0.03 = comprou há 1 ano
    """,
    source_features=["last_purchase_date"],
    transformation_fn=calculate_recency_score
)
```

## 📊 Monitoramento de Features

### Métricas Importantes

1. **Qualidade de Dados:**
   - Taxa de valores nulos
   - Taxa de valores fora do range esperado
   - Distribuição de valores

2. **Performance:**
   - Latência de leitura (p50, p95, p99)
   - Taxa de requisições
   - Taxa de erros

3. **Uso:**
   - Features mais consultadas
   - Features não utilizadas (candidatas a deprecação)
   - Padrões de acesso

### Implementação de Monitoramento

```python
import time
from functools import wraps

def monitor_feature_access(func):
    """Decorator para monitorar acesso a features"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            latency = time.time() - start_time
            # Log success
            log_metric("feature_access_success", 1, tags={"func": func.__name__})
            log_metric("feature_access_latency", latency, tags={"func": func.__name__})
            return result
        except Exception as e:
            # Log error
            log_metric("feature_access_error", 1, tags={"func": func.__name__, "error": str(e)})
            raise
    return wrapper

@monitor_feature_access
def get_online_features(group_name, entity_id):
    # ...
    pass
```

## 🔒 Segurança e Privacidade

### Dados Pessoais (PII)

```python
# Marcar features com PII
FeatureMetadata(
    name="customer_email",
    tags=["pii:true", "gdpr:sensitive"],
    # ...
)

# Hash de dados sensíveis
def hash_email(email: str) -> str:
    return hashlib.sha256(email.encode()).hexdigest()

# Anonimização
FeatureTransformation(
    name="anonymize_email",
    source_features=["email"],
    transformation_fn=hash_email
)
```

### Controle de Acesso

```python
# Documentar ownership
FeatureMetadata(
    name="credit_score",
    owner="risk-team@company.com",
    tags=["access:restricted", "team:risk"],
    # ...
)
```

## 🚀 Performance

### Otimização de Leituras

```python
# ✅ Buscar apenas features necessárias
needed_features = ["total_purchases", "avg_order_value"]
features = fs.get_online_features("customer_features", entity_id)
features = {k: v for k, v in features.items() if k in needed_features}

# ❌ Buscar todas as features se só precisa de algumas
all_features = fs.get_online_features("customer_features", entity_id)
```

### Batch Processing

```python
# ✅ Processar em lotes
entities = ["CUST001", "CUST002", "CUST003", ...]
batch_size = 100

for i in range(0, len(entities), batch_size):
    batch = entities[i:i+batch_size]
    process_batch(batch)

# ❌ Processar um por um
for entity in entities:
    process_single(entity)
```

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_feature_metadata(feature_name: str, entity: str):
    # Cache de metadados para evitar buscas repetidas
    return fs.get_feature_metadata(feature_name, entity)
```

## 🧪 Testes

### Testes de Features

```python
def test_feature_transformation():
    """Testa que a transformação produz o resultado esperado"""
    # Arrange
    data = {"total_spent": 1000.0, "total_purchases": 10}
    
    # Act
    result = avg_purchase_value_feature.compute(data)
    
    # Assert
    assert result == 100.0

def test_feature_validation():
    """Testa que a validação rejeita valores inválidos"""
    invalid_value = -10
    assert not feature._validate_value(invalid_value)

def test_feature_consistency():
    """Testa consistência entre online e offline"""
    entity_id = "TEST001"
    
    # Ingerir dados
    fs.ingest_features(group_name, entity_id, test_data)
    
    # Buscar online
    online = fs.get_online_features(group_name, entity_id)
    
    # Buscar offline
    offline = fs.get_offline_features(group_name)
    offline_row = offline[offline["entity_id"] == entity_id].iloc[0]
    
    # Verificar consistência
    assert online["feature_name"] == str(offline_row["feature_name"])
```

## 📚 Documentação

### Documentar Features

```python
FeatureMetadata(
    name="customer_churn_probability",
    description="""
    Probabilidade de churn do cliente nos próximos 30 dias.
    
    Calculada usando modelo de regressão logística baseado em:
    - Dias desde última compra
    - Taxa de abertura de emails
    - Número de tickets de suporte
    
    Valores:
        - 0.0-0.3: Baixo risco de churn
        - 0.3-0.7: Médio risco de churn
        - 0.7-1.0: Alto risco de churn
    
    Atualização: Diária às 2:00 AM UTC
    
    Uso recomendado:
        - Campanhas de retenção
        - Priorização de suporte
        - Personalização de ofertas
    """,
    feature_type=FeatureType.NUMERICAL,
    entity="customer",
    owner="ml-team@company.com",
    tags=["churn", "prediction", "critical"],
    version="1.0.0"
)
```

### README de Feature Group

Crie documentação para cada feature group importante:

```markdown
# Customer Behavior Features

## Descrição
Features comportamentais de clientes para modelos de recomendação e churn.

## Features

### customer_purchase_frequency
- **Tipo:** Numerical
- **Descrição:** Número médio de compras por mês
- **Janela:** 90 dias
- **Atualização:** Diária

### customer_avg_order_value
- **Tipo:** Numerical
- **Descrição:** Valor médio dos pedidos
- **Janela:** 90 dias
- **Atualização:** Diária

## Dependências
- Tabela: `orders`
- Tabela: `customers`

## Uso
```python
features = fs.get_online_features("customer_behavior", customer_id)
```

## Manutenção
- **Owner:** analytics-team@company.com
- **Slack:** #feature-store
- **Runbook:** [link]
```

## 🔄 Ciclo de Vida de Features

### 1. Desenvolvimento
- Criar em ambiente de dev
- Status: DRAFT
- Validar com dados históricos

### 2. Staging
- Testar em staging
- Validar com tráfego real (shadow mode)

### 3. Produção
- Deploy para produção
- Status: ACTIVE
- Monitorar métricas

### 4. Manutenção
- Atualizar documentação
- Ajustar validações conforme necessário
- Responder a alertas

### 5. Deprecação
- Comunicar aos stakeholders
- Status: DEPRECATED
- Manter por período de transição

### 6. Arquivamento
- Remover da produção
- Status: ARCHIVED
- Manter metadados para referência histórica

## 📋 Checklist para Nova Feature

Antes de adicionar uma nova feature à produção:

- [ ] Nome descritivo e claro
- [ ] Documentação completa
- [ ] Tags apropriadas
- [ ] Owner definido
- [ ] Validações implementadas
- [ ] Transformações testadas
- [ ] Testes unitários criados
- [ ] Versionamento definido
- [ ] Monitoramento configurado
- [ ] Revisão de código aprovada
- [ ] Documentação de uso criada
- [ ] Stakeholders notificados

## 🎓 Recursos Adicionais

- [Feature Engineering Book](https://www.amazon.com/Feature-Engineering-Machine-Learning-Principles/dp/1491953241)
- [Google ML Best Practices](https://developers.google.com/machine-learning/guides/rules-of-ml)
- [Uber's Michelangelo Platform](https://eng.uber.com/michelangelo-machine-learning-platform/)
- [Airbnb's Zipline](https://databricks.com/session/zipline-airbnbs-machine-learning-data-management-platform)
