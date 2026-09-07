# Gerando Classes Python a partir dos XSDs

O pacote `nfse.paulistana` utiliza a biblioteca `xsdata` para mapear de forma segura as regras e tipagens da Prefeitura de SP, descritas nos arquivos `.xsd` (XML Schemas).

Caso a Prefeitura atualize os schemas (por exemplo, ao lançar uma nova versão), você pode sobrescrever ou adicionar os novos arquivos na pasta `schemas-reformatributaria-v02-5` (ou criar uma nova) e pedir para o `xsdata` reconstruir as _dataclasses_ nativas do Python.

## Como gerar/atualizar os schemas:

1. **Ative o seu ambiente virtual:**
   Para garantir que você possui as bibliotecas necessárias instaladas, ative o ambiente virtual configurado no seu projeto.
   ```bash
   source .venv/bin/activate
   ```

2. **(Opcional) Instale o xsdata se não possuir:**
   ```bash
   pip install "xsdata[cli,lxml]"
   ```

3. **Rode o gerador apontando para a pasta XSD:**
   Na raiz do seu projeto (onde se encontram a pasta `nfse.paulistana`), execute:
   ```bash
   xsdata generate nfse/paulistana/xsd/schemas-reformatributaria-v02-5/ -p nfse.paulistana.schemas
   ```

   **O que este comando faz:**
   - Lê todos os XSDs dentro de `nfse/paulistana/xsd/schemas-reformatributaria-v02-5/`.
   - Lê as restrições, tipos e hierarquias (`min_occurs`, `pattern`, etc).
   - Cria um pacote limpo e tipado chamado `nfse.paulistana/schemas/` com todos os modelos equivalentes.

4. **Tratamento de Exceções (Ruff):**
   Durante a geração, o `xsdata` tentará utilizar o `ruff` (caso instalado) para formatar o código gerado. Caso o comando retorne algum erro sobre "ruff not found", basta assegurar que o caminho de binários do `.venv` está exportado (ex: `PATH=.venv/bin:$PATH`) ou rodar pelo binário exato `.venv/bin/xsdata ...`.


Se tudo der certo, você verá o terminal reportar `Analyzer output: X main and Y inner classes` informando quantas novas classes estão prontas para uso.

