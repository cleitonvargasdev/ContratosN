#!/usr/bin/env bash
# Execute no Ubuntu com os clientes PostgreSQL da mesma versao do servidor ou mais novos.
# Usa PGHOST/PGPORT/PGUSER/PGPASSFILE; nunca recebe senha na linha de comando.
set -euo pipefail
umask 077

source_db="${SOURCE_DB:-Contratos}"
cv_db="${CV_DB:-cv_financeiro}"
bc_db="${BC_DB:-bc_financeiro}"
registry_db="${REGISTRY_DB:-tenant_registry}"
backup_dir="${BACKUP_DIR:-./tenant-backups}"

for command_name in psql pg_dump pg_restore createdb; do
    command -v "$command_name" >/dev/null || { echo "Instale os clientes PostgreSQL: $command_name ausente." >&2; exit 1; }
done
for database in "$source_db" "$cv_db" "$bc_db" "$registry_db"; do
    [[ "$database" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] || { echo "Nome de banco invalido." >&2; exit 1; }
done
[[ "$source_db" != "$cv_db" && "$source_db" != "$bc_db" && "$source_db" != "$registry_db" && "$cv_db" != "$bc_db" && "$cv_db" != "$registry_db" && "$bc_db" != "$registry_db" ]] || { echo "Os quatro bancos devem ter nomes diferentes." >&2; exit 1; }

psql -X -v ON_ERROR_STOP=1 --dbname="$source_db" -Atc "SELECT current_database(), current_setting('server_version');"
for database in "$cv_db" "$bc_db" "$registry_db"; do
    exists=$(psql -X -v ON_ERROR_STOP=1 --dbname=postgres -Atc "SELECT 1 FROM pg_database WHERE datname='$database'")
    [[ "$exists" != "1" ]] || { echo "Banco $database ja existe. Nada sera sobrescrito." >&2; exit 1; }
done

mkdir -p -- "$backup_dir"
backup_file=$(mktemp "$backup_dir/origem-XXXXXXXX.dump")
echo "Gerando uma unica copia consistente da origem para restaurar nos dois bancos..."
pg_dump --dbname="$source_db" --format=custom --no-owner --no-acl --file="$backup_file"
pg_restore --list "$backup_file" >/dev/null

for database in "$cv_db" "$bc_db"; do
    echo "Criando e restaurando $database..."
    createdb --template=template0 "$database"
    pg_restore --exit-on-error --single-transaction --no-owner --no-acl --dbname="$database" "$backup_file"
    # Dados de negocio sao preservados. Apenas os agendamentos ficam desativados.
    psql -X -v ON_ERROR_STOP=1 --dbname="$database" <<'SQL'
UPDATE parametros SET score_atualizacao_automatica = false, whatsapp_cobranca_automatica = false;
SQL
done
createdb --template=template0 "$registry_db"

# Compara todas as tabelas publicas. Interrompe se a origem recebeu escritas durante a operacao.
# Para a copia definitiva, mantenha a aplicacao antiga parada durante todo este script.
counts_sql="SELECT format('SELECT %L, count(*) FROM %I.%I;', tablename, schemaname, tablename) FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"
count_queries=$(psql -X -v ON_ERROR_STOP=1 --dbname="$source_db" -Atc "$counts_sql")
source_counts=$(printf '%s\n' "$count_queries" | psql -X -v ON_ERROR_STOP=1 --dbname="$source_db" -At)
for database in "$cv_db" "$bc_db"; do
    target_counts=$(printf '%s\n' "$count_queries" | psql -X -v ON_ERROR_STOP=1 --dbname="$database" -At)
    [[ "$source_counts" == "$target_counts" ]] || { echo "Contagens divergem em $database. Nao ative os tenants; confira escritas na origem." >&2; exit 1; }
    echo "$database: contagens das tabelas conferidas."
done
echo "Copia concluida. Backup preservado em $backup_file. Origem $source_db preservada."
echo "Os bancos ainda precisam ser cadastrados no registro central antes de ativar TENANCY_ENABLED."
