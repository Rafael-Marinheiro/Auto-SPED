"""Módulo para conexão e consultas ao banco de dados Firebird (DADOS.FDB)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import fdb


class DatabaseConnection:
    """Gerencia a conexão com o banco de dados Firebird."""

    def __init__(
        self,
        db_path: str,
        user: str = "SYSDBA",
        password: str = "masterkey",
        client_library: str | None = None,
    ):
        self.db_path = db_path
        self.user = user
        self.password = password
        self.client_library = client_library
        self.connection: Optional[fdb.Connection] = None

    _client_loaded = False
    _loaded_client_path: str | None = None

    @staticmethod
    def _canonical_client_path(path: str) -> str:
        """Normaliza um caminho para comparar bibliotecas já carregadas."""
        return os.path.normcase(os.path.abspath(os.path.expanduser(path)))

    def _ensure_client_loaded(self) -> None:
        """Carrega a biblioteca cliente do Firebird conforme o ambiente."""
        if DatabaseConnection._client_loaded:
            if self.client_library:
                requested_path = self._canonical_client_path(self.client_library)
                loaded_path = DatabaseConnection._loaded_client_path
                if loaded_path and requested_path != loaded_path:
                    raise RuntimeError(
                        "O fbclient já carregado neste processo é "
                        f"'{loaded_path}'. Para usar '{requested_path}', encerre e "
                        "execute o aplicativo novamente."
                    )
            return

        env_path = os.environ.get("FBCLIENT_PATH")
        candidates = []
        if self.client_library:
            explicit_path = Path(self.client_library)
            if not explicit_path.is_file():
                raise FileNotFoundError(
                    f"Biblioteca cliente Firebird não encontrada: {explicit_path}"
                )
            candidates.append(str(explicit_path))
        elif env_path:
            candidates.append(env_path)

        if os.name == "nt":
            candidates.extend([
                r"C:\Program Files\Firebird\Firebird_2_5\bin\fbclient.dll",
                r"C:\Program Files (x86)\Firebird\Firebird_2_5\bin\fbclient.dll",
            ])
            default_name = "fbclient.dll"
        else:
            candidates.extend([
                "/usr/lib/libfbclient.so",
                "/usr/lib/firebird/3.0/lib/libfbclient.so",
                "/usr/lib/x86_64-linux-gnu/libfbclient.so",
                "/usr/lib/x86_64-linux-gnu/libfbclient.so.3",
                "/usr/lib/x86_64-linux-gnu/libfbclient.so.3.0.11",
                "/opt/firebird/lib/libfbclient.so",
                "/usr/local/lib/libfbclient.so",
            ])
            default_name = "libfbclient.so"

        for candidate in candidates:
            candidate_path = Path(candidate)
            if candidate_path.exists():
                try:
                    fdb.load_api(str(candidate_path))
                    DatabaseConnection._client_loaded = True
                    DatabaseConnection._loaded_client_path = self._canonical_client_path(
                        str(candidate_path)
                    )
                    return
                except Exception as error:
                    if self.client_library:
                        raise FileNotFoundError(
                            "Não foi possível carregar a biblioteca cliente Firebird "
                            f"informada: {candidate_path}. Verifique a versão e a "
                            f"arquitetura (32/64 bits). Detalhe: {error}"
                        ) from error
                    continue

        # Última tentativa: deixa o driver procurar pelo nome padrão.
        try:
            fdb.load_api(default_name)
        except Exception:
            # Se ainda falhar, deixe o erro ocorrer no connect() com mensagem clara.
            raise FileNotFoundError(
                "Biblioteca cliente do Firebird não encontrada. "
                "Defina a variável de ambiente FBCLIENT_PATH apontando para o fbclient."
            )
        DatabaseConnection._client_loaded = True
        DatabaseConnection._loaded_client_path = default_name

    def connect(self) -> None:
        """Estabelece conexão com o banco de dados."""
        try:
            self._ensure_client_loaded()
            db_file = Path(self.db_path)
            if db_file.exists() and os.name != "nt":
                dsn = str(db_file.resolve())
            else:
                dsn = self.db_path
            self.connection = fdb.connect(
                dsn=dsn,
                user=self.user,
                password=self.password,
                charset="WIN1252"
            )
        except (fdb.DatabaseError, FileNotFoundError, RuntimeError) as e:
            raise ConnectionError(f"Erro ao conectar ao banco de dados: {e}")

    def disconnect(self) -> None:
        """Fecha a conexão com o banco de dados."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Executa uma consulta SQL e retorna os resultados."""
        if not self.connection:
            raise ConnectionError("Conexão não estabelecida. Chame connect() primeiro.")

        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results
        finally:
            cursor.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


class SpedDataExtractor:
    """Extrai dados do banco para geração do SPED."""

    def __init__(self, db_path: str, client_library: str | None = None):
        self.db = DatabaseConnection(db_path, client_library=client_library)

    def get_company_info(self) -> Dict[str, str]:
        """Obtém informações da empresa."""
        query = """
        SELECT
            CNPJ,
            RAZAO as NOME,
            FANTASIA,
            IE,
            CEP,
            ENDERECO as "END",
            NUMERO as NUM,
            COMPLEMENTO as COMPL,
            BAIRRO,
            FONE,
            FAX,
            EMAIL,
            ID_CIDADE as COD_MUN,
            IM,
            UF
        FROM EMPRESA
        """
        with self.db:
            results = self.db.execute_query(query)
            if not results:
                raise ValueError("Nenhuma empresa encontrada.")
            return results[0]

    def get_accountant_info(self) -> Dict[str, str]:
        """Obtém informações do contador."""
        query = """
        SELECT
            NOME,
            CPF,
            CRC,
            CNPJ,
            CEP,
            ENDERECO as "END",
            NUMERO as NUM,
            COMPLEMENTO as COMPL,
            BAIRRO,
            FONE,
            FAX,
            EMAIL,
            COD_MUN
        FROM CONTADOR
        """
        with self.db:
            results = self.db.execute_query(query)
            if not results:
                raise ValueError("Nenhum contador encontrado.")
            # Mapear os campos corretos
            row = results[0]
            return {
                'NOME': row['NOME'],
                'CPF': row['CPF'],
                'CRC': row['CRC'],
                'CNPJ': row['CNPJ'],
                'CEP': row['CEP'],
                'END': row['END'],
                'NUM': row['NUM'],
                'COMPL': row['COMPL'],
                'BAIRRO': row['BAIRRO'],
                'FONE': row['FONE'],
                'FAX': row['FAX'],
                'EMAIL': row['EMAIL'],
                'COD_MUN': row['COD_MUN']
            }

    def get_participants(self) -> List[Dict[str, str]]:
        """Obtém todos os participantes (fornecedores/clientes) ativos."""
        query = """
        SELECT
            P.CODIGO as COD_PART,
            P.RAZAO as NOME,
            P.CNPJ as CNPJ,
            P.IE as IE,
            COALESCE(
                NULLIF(P.CODMUN, 0),
                (
                    SELECT FIRST 1 C.CODIGO
                    FROM CIDADE C
                    WHERE UPPER(C.DESCRICAO) = UPPER(P.MUNICIPIO)
                      AND C.UF = P.UF
                )
            ) as COD_MUN,
            P.ENDERECO as "END",
            P.NUMERO as NUM,
            P.COMPLEMENTO as COMPL,
            P.BAIRRO as BAIRRO
        FROM PESSOA P
        WHERE P.ATIVO = 'S'
        """
        with self.db:
            return self.db.execute_query(query)

    def get_products(self) -> List[Dict[str, str]]:
        """Obtém todos os produtos ativos."""
        query = """
        SELECT
            PR.CODIGO as COD_ITEM,
            PR.DESCRICAO as DESCR_ITEM,
            PR.UNIDADE as UNID_INV,
            PR.TIPO as TIPO_ITEM,
            PR.NCM as COD_NCM,
            PR.CEST as CEST,
            PR.ALIQ_ICM as ALIQ_ICMS
        FROM PRODUTO PR
        """
        with self.db:
            return self.db.execute_query(query)

    def get_units(self) -> List[Dict[str, str]]:
        """Obtém todas as unidades de medida dos produtos ativos."""
        query = """
        SELECT DISTINCT
            PR.UNIDADE as UNID,
            'UNIDADE' as DESCR
        FROM PRODUTO PR
        """
        with self.db:
            return self.db.execute_query(query)

    def get_invoices(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Obtém notas fiscais do período (NFE e NFCE)."""
        query = """
        SELECT
            NF.NUMERO as NUM_DOC,
            NF.SERIE as SER,
            NF.CHAVE as CHV_NFE,
            NF.DATA_EMISSAO as DT_DOC,
            NF.DATA_SAIDA as DT_E_S,
            NF.TOTAL as VL_DOC,
            NF.DESCONTO as VL_DESC,
            NF.FRETE as VL_FRT,
            NF.SEGURO as VL_SEG,
            NF.OUTROS as VL_OUT_DA,
            NF.TOTAL as VL_MERC,
            NF.BASEICMS as VL_BC_ICMS,
            NF.TOTALICMS as VL_ICMS,
            NF.TOTAL_IPI as VL_IPI,
            NF.TOTALICMSPIS as VL_PIS,
            NF.TOTALICMSCOFINS as VL_COFINS,
            P.CODIGO as COD_PART,
            CASE WHEN NF.MOVIMENTO = 'S' THEN '1' ELSE '0' END as IND_OPER,
            NF.TIPO_EMISSAO as IND_EMIT,
            NF.MODELO as COD_MOD,
            NF.SITUACAO as COD_SIT,
            VM.FORMA_PAGAMENTO as FORMA_PAGAMENTO
        FROM NFE_MASTER NF
        INNER JOIN PESSOA P ON NF.ID_CLIENTE = P.CODIGO
        LEFT JOIN VENDAS_MASTER VM ON VM.CODIGO = NF.FKVENDA
        WHERE NF.DATA_EMISSAO BETWEEN ? AND ?
        UNION ALL
        SELECT
            NF.NUMERO as NUM_DOC,
            NF.SERIE as SER,
            NF.CHAVE as CHV_NFE,
            NF.DATA_EMISSAO as DT_DOC,
            NF.DATA_SAIDA as DT_E_S,
            NF.TOTAL as VL_DOC,
            NF.DESCONTO as VL_DESC,
            0 as VL_FRT,
            0 as VL_SEG,
            NF.OUTROS as VL_OUT_DA,
            NF.TOTAL as VL_MERC,
            NF.BASEICMS as VL_BC_ICMS,
            NF.TOTALICMS as VL_ICMS,
            0 as VL_IPI,
            NF.TOTALICMSPIS as VL_PIS,
            NF.TOTALICMSCOFINS as VL_COFINS,
            P.CODIGO as COD_PART,
            '1' as IND_OPER,
            '1' as IND_EMIT,
            NF.MODELO as COD_MOD,
            NF.SITUACAO as COD_SIT,
            VM.FORMA_PAGAMENTO as FORMA_PAGAMENTO
        FROM NFCE_MASTER NF
        INNER JOIN PESSOA P ON NF.ID_CLIENTE = P.CODIGO
        LEFT JOIN VENDAS_MASTER VM ON VM.CODIGO = NF.FK_VENDA
        WHERE NF.DATA_EMISSAO BETWEEN ? AND ?
        ORDER BY 4, 1
        """
        with self.db:
            return self.db.execute_query(query, (start_date, end_date, start_date, end_date))

    def get_invoice_items(self, invoice_number: str) -> List[Dict[str, Any]]:
        """Obtém itens de uma nota fiscal (NFE e NFCE)."""
        query = """
        SELECT
            ND.ITEM as NUM_ITEM,
            PR.CODIGO as COD_ITEM,
            ND.QTD as QTD,
            PR.UNIDADE as UNID,
            ND.VL_OPERACAO as VL_ITEM,
            ND.TOTAL as VL_TOTAL,
            ND.DESCONTO as VL_DESC,
            ND.CST as CST_ICMS,
            ND.CFOP as CFOP,
            ND.BASE_ICMS as VL_BC_ICMS,
            ND.ALIQ_ICMS as ALIQ_ICMS,
            ND.VALOR_ICMS as VL_ICMS,
            ND.CST_IPI as CST_IPI,
            ND.VALOR_IPI as VL_IPI,
            ND.CST_PIS as CST_PIS,
            ND.BASE_PIS_ICMS as VL_BC_PIS,
            ND.ALIQ_PIS_ICMS as ALIQ_PIS,
            ND.VALOR_PIS_ICMS as VL_PIS,
            ND.CST_COFINS as CST_COFINS,
            ND.BASE_COFINS_ICMS as VL_BC_COFINS,
            ND.ALIQ_COFINS_ICMS as ALIQ_COFINS,
            ND.VALOR_COFINS_ICMS as VL_COFINS
        FROM NFE_DETALHE ND
        INNER JOIN PRODUTO PR ON ND.ID_PRODUTO = PR.CODIGO
        WHERE ND.FKNFE = ?
        UNION ALL
        SELECT
            ND.ITEM as NUM_ITEM,
            PR.CODIGO as COD_ITEM,
            ND.QTD as QTD,
            ND.UNIDADE as UNID,
            ND.VALOR_ITEM as VL_ITEM,
            ND.VALOR_ITEM as VL_TOTAL,
            ND.VDESCONTO as VL_DESC,
            ND.CST as CST_ICMS,
            ND.CFOP as CFOP,
            ND.BASE_ICMS as VL_BC_ICMS,
            ND.ALIQ_ICMS as ALIQ_ICMS,
            ND.VALOR_ICMS as VL_ICMS,
            0 as CST_IPI,
            0 as VL_IPI,
            ND.CST_PIS as CST_PIS,
            ND.BASE_PIS_ICMS as VL_BC_PIS,
            ND.ALIQ_PIS_ICMS as ALIQ_PIS,
            ND.VALOR_PIS_ICMS as VL_PIS,
            ND.CST_COFINS as CST_COFINS,
            ND.BASE_COFINS_ICMS as VL_BC_COFINS,
            ND.ALIQ_COFINS_ICMS as ALIQ_COFINS,
            ND.VALOR_COFINS_ICMS as VL_COFINS
        FROM NFCE_DETALHE ND
        INNER JOIN PRODUTO PR ON ND.ID_PRODUTO = PR.CODIGO
        WHERE ND.FKVENDA = ?
        ORDER BY 1
        """
        with self.db:
            return self.db.execute_query(query, (invoice_number, invoice_number))

    def resolve_invoice_ids(self, cod_mod: str, serie: str, num_doc: str) -> Dict[str, Any]:
        """Resolve DOC_ID e VENDA_ID a partir de modelo/série/número."""
        s = str(serie).strip()
        n = str(num_doc).strip()
        if str(cod_mod).strip() == "65":
            query = "SELECT FIRST 1 CODIGO as DOC_ID, FK_VENDA as VENDA_ID FROM NFCE_MASTER WHERE SERIE = ? AND NUMERO = ? ORDER BY DATA_EMISSAO DESC, CODIGO DESC"
        else:
            query = "SELECT FIRST 1 CODIGO as DOC_ID, FKVENDA as VENDA_ID FROM NFE_MASTER WHERE SERIE = ? AND NUMERO = ? ORDER BY DATA_EMISSAO DESC, CODIGO DESC"
        with self.db:
            rows = self.db.execute_query(query, (s, n))
            return rows[0] if rows else {"DOC_ID": None, "VENDA_ID": None}

    def get_invoice_items_by_ids(self, cod_mod: str, doc_id: str | int, venda_id: str | int, ind_oper: str | None = None, origem: str | None = None) -> List[Dict[str, Any]]:
        """Obtém itens usando FKs corretas (sem misturar compra com venda)."""
        cod_mod_norm = str(cod_mod).strip()
        origem_norm = str(origem or "").strip().upper()
        if cod_mod_norm == "65":
            query = """
            SELECT
                ND.ITEM as NUM_ITEM,
                PR.CODIGO as COD_ITEM,
                ND.QTD as QTD,
                ND.UNIDADE as UNID,
                ND.VALOR_ITEM as VL_ITEM,
                ND.VALOR_ITEM as VL_TOTAL,
                ND.VDESCONTO as VL_DESC,
                ND.CST as CST_ICMS,
                ND.CFOP as CFOP,
                ND.BASE_ICMS as VL_BC_ICMS,
                ND.ALIQ_ICMS as ALIQ_ICMS,
                ND.VALOR_ICMS as VL_ICMS,
                0 as CST_IPI,
                0 as VL_IPI,
                ND.CST_PIS as CST_PIS,
                ND.BASE_PIS_ICMS as VL_BC_PIS,
                ND.ALIQ_PIS_ICMS as ALIQ_PIS,
                ND.VALOR_PIS_ICMS as VL_PIS,
                ND.CST_COFINS as CST_COFINS,
                ND.BASE_COFINS_ICMS as VL_BC_COFINS,
                ND.ALIQ_COFINS_ICMS as ALIQ_COFINS,
                ND.VALOR_COFINS_ICMS as VL_COFINS
            FROM NFCE_DETALHE ND
            INNER JOIN PRODUTO PR ON ND.ID_PRODUTO = PR.CODIGO
            WHERE ND.FKVENDA = ?
            ORDER BY 1
            """
            with self.db:
                return self.db.execute_query(query, (doc_id or venda_id,))
        else:
            is_compra = origem_norm == "COMPRA"
            if is_compra:
                query = """
            SELECT
                CI.ITEM as NUM_ITEM,
                PR.CODIGO as COD_ITEM,
                CI.QTD as QTD,
                PR.UNIDADE as UNID,
                CI.TOTAL_COMPRA as VL_ITEM,
                CI.TOTAL_COMPRA as VL_TOTAL,
                CI.DESCONTO as VL_DESC,
                CI.CST_ICM as CST_ICMS,
                CI.CFOP as CFOP,
                CI.BASE_ICMS as VL_BC_ICMS,
                CI.ALIQ_ICMS as ALIQ_ICMS,
                CI.VL_ICMS as VL_ICMS,
                CI.CST_IPI as CST_IPI,
                CI.VL_IPI as VL_IPI,
                CI.CST_PIS as CST_PIS,
                CI.BASE_PIS as VL_BC_PIS,
                CI.ALIQ_PIS as ALIQ_PIS,
                CI.VL_PIS as VL_PIS,
                CI.CST_COF as CST_COFINS,
                CI.BASE_COF as VL_BC_COFINS,
                CI.ALIQ_COF as ALIQ_COFINS,
                CI.VL_COF as VL_COFINS
            FROM COMPRA_ITENS CI
            INNER JOIN PRODUTO PR ON CI.FK_PRODUTO = PR.CODIGO
            WHERE CI.FK_COMPRA = ?
            ORDER BY 1
                """
                params: tuple[Any, ...] = (doc_id,)
            else:
                query = """
            SELECT
                ND.ITEM as NUM_ITEM,
                PR.CODIGO as COD_ITEM,
                ND.QTD as QTD,
                PR.UNIDADE as UNID,
                ND.VL_OPERACAO as VL_ITEM,
                ND.TOTAL as VL_TOTAL,
                ND.DESCONTO as VL_DESC,
                ND.CST as CST_ICMS,
                ND.CFOP as CFOP,
                ND.BASE_ICMS as VL_BC_ICMS,
                ND.ALIQ_ICMS as ALIQ_ICMS,
                ND.VALOR_ICMS as VL_ICMS,
                ND.CST_IPI as CST_IPI,
                ND.VALOR_IPI as VL_IPI,
                ND.CST_PIS as CST_PIS,
                ND.BASE_PIS_ICMS as VL_BC_PIS,
                ND.ALIQ_PIS_ICMS as ALIQ_PIS,
                ND.VALOR_PIS_ICMS as VL_PIS,
                ND.CST_COFINS as CST_COFINS,
                ND.BASE_COFINS_ICMS as VL_BC_COFINS,
                ND.ALIQ_COFINS_ICMS as ALIQ_COFINS,
                ND.VALOR_COFINS_ICMS as VL_COFINS
            FROM NFE_DETALHE ND
            INNER JOIN PRODUTO PR ON ND.ID_PRODUTO = PR.CODIGO
            WHERE ND.FKNFE = ?
            ORDER BY 1
                """
                params = (doc_id,)
            with self.db:
                return self.db.execute_query(query, params)

    def get_invoices(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Obtém notas fiscais do período (NFE, NFCE e COMPRA) com origem explícita."""
        query = """
        SELECT
            NF.NUMERO as NUM_DOC,
            NF.SERIE as SER,
            NF.CHAVE as CHV_NFE,
            NF.DATA_EMISSAO as DT_DOC,
            NF.DATA_SAIDA as DT_E_S,
            NF.TOTAL as VL_DOC,
            NF.DESCONTO as VL_DESC,
            NF.FRETE as VL_FRT,
            NF.SEGURO as VL_SEG,
            NF.OUTROS as VL_OUT_DA,
            NF.SUBTOTAL as VL_MERC,
            NF.BASEICMS as VL_BC_ICMS,
            NF.TOTALICMS as VL_ICMS,
            NF.TOTAL_IPI as VL_IPI,
            NF.TOTALICMSPIS as VL_PIS,
            NF.TOTALICMSCOFINS as VL_COFINS,
            P.CODIGO as COD_PART,
            CASE WHEN NF.MOVIMENTO = 'S' THEN '1' ELSE '0' END as IND_OPER,
            NF.TIPO_EMISSAO as IND_EMIT,
            NF.MODELO as COD_MOD,
            NF.SITUACAO as COD_SIT,
            VM.FORMA_PAGAMENTO as FORMA_PAGAMENTO,
            NF.CODIGO as DOC_ID,
            NF.FKVENDA as VENDA_ID,
            'NFE' as ORIGEM
        FROM NFE_MASTER NF
        INNER JOIN PESSOA P ON NF.ID_CLIENTE = P.CODIGO
        LEFT JOIN VENDAS_MASTER VM ON VM.CODIGO = NF.FKVENDA
        WHERE NF.DATA_EMISSAO BETWEEN ? AND ?
          AND COALESCE(NF.SITUACAO, 0) NOT IN (3, 5)
        UNION ALL
        SELECT
            NF.NUMERO as NUM_DOC,
            NF.SERIE as SER,
            NF.CHAVE as CHV_NFE,
            NF.DATA_EMISSAO as DT_DOC,
            NF.DATA_SAIDA as DT_E_S,
            NF.TOTAL as VL_DOC,
            NF.DESCONTO as VL_DESC,
            0 as VL_FRT,
            0 as VL_SEG,
            NF.OUTROS as VL_OUT_DA,
            NF.SUBTOTAL as VL_MERC,
            NF.BASEICMS as VL_BC_ICMS,
            NF.TOTALICMS as VL_ICMS,
            0 as VL_IPI,
            NF.TOTALICMSPIS as VL_PIS,
            NF.TOTALICMSCOFINS as VL_COFINS,
            P.CODIGO as COD_PART,
            '1' as IND_OPER,
            '1' as IND_EMIT,
            NF.MODELO as COD_MOD,
            NF.SITUACAO as COD_SIT,
            VM.FORMA_PAGAMENTO as FORMA_PAGAMENTO,
            NF.CODIGO as DOC_ID,
            NF.FK_VENDA as VENDA_ID,
            'NFCE' as ORIGEM
        FROM NFCE_MASTER NF
        INNER JOIN PESSOA P ON NF.ID_CLIENTE = P.CODIGO
        LEFT JOIN VENDAS_MASTER VM ON VM.CODIGO = NF.FK_VENDA
        WHERE NF.DATA_EMISSAO BETWEEN ? AND ?
        UNION ALL
        SELECT
            C.NR_NOTA       as NUM_DOC,
            C.SERIE         as SER,
            C.CHAVE         as CHV_NFE,
            C.DTEMISSAO     as DT_DOC,
            C.DTENTRADA     as DT_E_S,
            C.TOTAL         as VL_DOC,
            C.DESCONTO      as VL_DESC,
            C.FRETE         as VL_FRT,
            C.SEGURO        as VL_SEG,
            C.DESPESAS      as VL_OUT_DA,
            C.TOTAL         as VL_MERC,
            C.BASE_ICM      as VL_BC_ICMS,
            C.TOTAL_ICM     as VL_ICMS,
            C.TOTAL_IPI     as VL_IPI,
            C.TOTAL_PIS     as VL_PIS,
            C.TOTAL_COF     as VL_COFINS,
            P.CODIGO        as COD_PART,
            '0'             as IND_OPER,
            '1'             as IND_EMIT,
            C.MODELO        as COD_MOD,
            '00'            as COD_SIT,
            NULL            as FORMA_PAGAMENTO,
            C.ID            as DOC_ID,
            NULL            as VENDA_ID,
            'COMPRA'        as ORIGEM
        FROM COMPRA C
        INNER JOIN PESSOA P ON C.FORNECEDOR = P.CODIGO
        WHERE C.DTENTRADA BETWEEN ? AND ?
        ORDER BY 4, 1
        """
        with self.db:
            return self.db.execute_query(
                query,
                (start_date, end_date, start_date, end_date, start_date, end_date),
            )
