​✨ O que ele faz?
​Gerador de Chaves: Cria chaves privadas, públicas e endereços (Legacy e SegWit) a partir de números decimais.
​Verificador de Saldo: Consulta a blockchain em tempo real para ver se a carteira tem saldo (com animação de loading).
​Conversor: Transforma chaves WIF ou Hexadecimal em endereços.
​Estrategista (Sniper): Calcula fatias exatas de intervalos (Ranges) para Puzzles.
​Integrador: Gera linhas de comando prontas para copiar e colar no BitCrack e KeyHunt.
​🚀 Instalação Passo a Passo
​Siga o tutorial abaixo de acordo com o seu sistema. Você só precisa fazer isso uma vez.
​🐧 Opção 1: Linux (Ubuntu, Debian, Kali, Mint) ou WSL (Windows)
​Se você usa Linux direto ou o WSL dentro do Windows, abra seu terminal e digite os comandos abaixo, um por um:
​1. Atualize o sistema:
```bash
sudo apt update && sudo apt upgrade -y
```
2. Instale o Python e o gerenciador de pacotes:
3. ```bash
   sudo apt install python3 python3-pip -y
  
3. Instale as bibliotecas necessárias:
(Aqui está a mágica. Este comando instala o rich para o visual e as ferramentas de criptografia).
```bash
pip3 install rich requests ecdsa base58 bech32
```
📱 Opção 2: Termux (Android)
​Se você está rodando pelo celular via Termux:
​1. Atualize o Termux:
```bash
pkg update && pkg upgrade -y
```
2. Instale o Python:
3. ```bash
   pkg install python -y
   ```
   
(Se ele perguntar algo durante a instalação, digite Y e dê Enter).

​3. Instale as bibliotecas:
```bash
pip install rich requests ecdsa base58 bech32
```

🎮 Como Usar
​Baixe ou crie o arquivo do script (ex: gerador.py) na sua pasta.
​Para rodar, digite no terminal:
```bash
python3 gerador.py
```
Entendendo o Menu
​1. Gerar chave por número: Você digita um número (ex: 200) e ele monta uma tabela bonita com todos os dados e verifica o saldo.
​2. Gerar chaves em intervalo: Para testes rápidos (ex: do 1 ao 50).
​3. Converter chave: Útil para transformar sua chave privada em endereço.
​4. Calculadora de Range: Você cola o range gigante do puzzle, corta ele em uma porcentagem (ex: 50%) e ele te dá o comando para o BitCrack começar dali.
​5. Zona de Busca: A ferramenta mais precisa. Você diz "Comece em 60% e ande apenas 1%". Ele gera o comando focado nesse trecho.
​🔧 Integração com BitCrack e KeyHunt
​Este script facilita sua vida gerando o comando exato para as duas principais ferramentas de busca. Veja a diferença de como usar cada uma:
​1. Para usuários do KeyHunt 🟢
​O KeyHunt funciona lendo endereços de um arquivo de texto (.txt).
•O que o programa vai te pedir: O nome do arquivo onde você salvou o endereço.
Onde o arquivo deve estar: O script gera o comando assumindo que seu arquivo está na pasta tests/.
•Exemplo:
1. Você escolhe a opção KeyHunt no menu.
2. O programa pergunta: "Nome do arquivo com o endereço alvo (sem .txt)".
3. Você digita: puzzle66.
4. O programa gera:
```bash
./keyhunt -m address -f tests/puzzle66.txt -r 2000...:3FFF... -l compress
```
5. Você copia isso e cola no terminal do KeyHunt.

2. Para usuários do BitCrack 🔴
​O BitCrack (versão CUDA/OpenCL) aceita o endereço diretamente na linha de comando,
sem precisar de arquivo de texto para buscas simples.
•O que o programa vai te pedir: O código da carteira (o endereço público comprimido).
• Exemplo:
1. Você escolhe a opção BitCrack no menu.
2. O programa pergunta: "Qual o endereço alvo? (Comprimido)".
3. Você cola a carteira:

13zb1hQbWVsc2S7ZTZnP2G4undNNpdh5so

4. O programa gera:

```bash
./bitcrack -b 60 -t 256 -p 512 --keyspace 2000...:3FFF... 13zb1hQbWVsc2S7ZTZnP2G4undNNpdh5so
```

5. Você copia e cola no terminal onde o BitCrack está instalado.

💡 Dica Importante sobre as Pastas
​O script assume que você vai rodar o comando gerado na pasta onde as ferramentas estão instaladas.
​Se o script gerou ./keyhunt, certifique-se de estar na pasta do KeyHunt.
​Se o script gerou ./bitcrack, certifique-se de estar na pasta do BitCrack.
