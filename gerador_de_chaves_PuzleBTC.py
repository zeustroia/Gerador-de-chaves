import hashlib
import base58
import bech32
import requests
import random
import time
from ecdsa import SECP256k1, SigningKey

# Importações da RICH
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich import box

# Inicializa o console global
console = Console()

# --- FUNÇÕES AUXILIARES ---

def verificar_saldo(endereco):
    """
    Verifica o saldo usando a API e retorna uma string formatada e colorida.
    Agora com Spinner de carregamento visual.
    """
    url = f"https://blockstream.info/api/address/{endereco}"
    try:
        # Spinner visual enquanto faz a requisição
        with console.status(f"[bold green]Consultando saldo para {endereco}...", spinner="dots"):
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            dados = response.json()
            
        saldo_satoshi = dados['chain_stats']['funded_txo_sum'] - dados['chain_stats']['spent_txo_sum']
        saldo_btc = saldo_satoshi / 100_000_000.0
        
        if saldo_btc > 0:
            return f"[bold green]{saldo_btc:.8f} BTC[/] 💰"
        else:
            return "[dim white]0.00000000 BTC[/]"
            
    except Exception:
        return "[bold red]Erro/Offline[/]"

def gerar_comandos_externos(range_gerado):
    """
    Gera os comandos formatados dentro de um Painel bonito.
    """
    console.print()
    console.rule("[bold yellow]Gerador de Comandos Externos[/]")
    
    console.print("[yellow]Deseja gerar o comando pronto para qual ferramenta?[/]")
    console.print("1. KeyHunt (Requer arquivo .txt)")
    console.print("2. BitCrack (Requer endereço da carteira)")
    console.print("3. Nenhuma (Voltar)")
    
    escolha = Prompt.ask("[bold cyan]Sua escolha[/]", choices=["1", "2", "3"], default="3")
    
    if escolha == '1': # KeyHunt
        nome_arquivo = Prompt.ask("[bold]Nome do arquivo com o endereço alvo (sem .txt)[/]")
        if not nome_arquivo.lower().endswith('.txt'):
            nome_arquivo = f"{nome_arquivo}.txt"

        comando = f"./keyhunt -m address -f tests/{nome_arquivo} -r {range_gerado} -l compress"
        titulo = "Comando KeyHunt"

    elif escolha == '2': # BitCrack
        endereco_alvo = Prompt.ask("[bold]Qual o endereço alvo? (Comprimido)[/]")
        # Sintaxe solicitada: -b 60 -t 256 -p 512 --keyspace RANGE ENDERECO
        comando = f"./bitcrack -b 60 -t 256 -p 512 --keyspace {range_gerado} {endereco_alvo}"
        titulo = "Comando BitCrack"
        
    else:
        return

    # Exibe o comando dentro de um painel copiável
    painel = Panel(
        f"[bold green]{comando}[/]",
        title=f"[bold cyan]{titulo}[/]",
        subtitle="[dim]Copie e cole no seu terminal[/]",
        border_style="green"
    )
    console.print(painel)


# --- FUNÇÕES PRINCIPAIS ---

def gerar_chave(numero):
    """Gera dados da chave e exibe em uma tabela Rich."""
    try:
        chave_privada_bytes = numero.to_bytes(32, 'big')
        chave_privada_hex = chave_privada_bytes.hex()
        sk = SigningKey.from_string(chave_privada_bytes, curve=SECP256k1)
        vk = sk.get_verifying_key()
        chave_publica_comprimida = vk.to_string("compressed")
        
        # Hashing
        sha256_bpk = hashlib.sha256(chave_publica_comprimida)
        ripemd160_bpk = hashlib.new("ripemd160")
        ripemd160_bpk.update(sha256_bpk.digest())
        hashed_public_key = ripemd160_bpk.digest()
        
        # Endereços
        endereco_legacy = base58.b58encode_check(b"\x00" + hashed_public_key).decode('utf-8')
        witness_program = bech32.convertbits(hashed_public_key, 8, 5)
        endereco_segwit = bech32.bech32_encode('bc', [0] + witness_program)
        
        # WIF
        wif_bytes = b"\x80" + chave_privada_bytes + b"\x01"
        chave_wif = base58.b58encode_check(wif_bytes).decode('utf-8')

        # Consulta Saldos
        saldo_legacy = verificar_saldo(endereco_legacy)
        saldo_segwit = verificar_saldo(endereco_segwit)

        # CRIAÇÃO DA TABELA VISUAL
        tabela = Table(title=f"Resultados para a Chave Decimal: {numero}", box=box.ROUNDED)

        tabela.add_column("Tipo", style="cyan", no_wrap=True)
        tabela.add_column("Dados", style="white")
        tabela.add_column("Saldo", justify="right")

        tabela.add_row("Privada (Hex)", chave_privada_hex, "-")
        tabela.add_row("Privada (WIF)", chave_wif, "-")
        tabela.add_section()
        tabela.add_row("Legacy (P2PKH)", endereco_legacy, saldo_legacy)
        tabela.add_row("SegWit (Bech32)", endereco_segwit, saldo_segwit)

        console.print(tabela)

    except Exception as e:
        console.print(f"[bold red]Erro ao gerar chave: {e}[/]")

def converter_chave():
    console.rule("[bold blue]Conversor de Chaves[/]")
    chave_input = Prompt.ask("Digite a [bold]chave privada[/] (WIF ou Hex)").strip()
    
    try:
        chave_privada_bytes = None
        if chave_input.startswith(('K', 'L', '5')):
            chave_decodificada = base58.b58decode_check(chave_input)
            chave_privada_bytes = chave_decodificada[1:33]
            console.print("[italic green]Formato WIF detectado...[/]")
        else:
            if len(chave_input) > 64:
                console.print("[bold red]Erro: Hexadecimal muito longo![/]")
                return
            chave_hex_completa = chave_input.zfill(64)
            chave_privada_bytes = bytes.fromhex(chave_hex_completa)
            console.print("[italic green]Formato HEX detectado...[/]")
            
        numero_decimal = int.from_bytes(chave_privada_bytes, 'big')
        gerar_chave(numero_decimal)
        
    except Exception as e:
        console.print(f"[bold red]Erro ao converter: {e}[/]")

def calculadora_range_inteligente():
    console.rule("[bold magenta]Calculadora de Range (Cortadora)[/]")
    
    range_input = Prompt.ask("Digite o range [bold](INICIO:FIM)[/]").strip().lower()
    try:
        partes = range_input.split(':')
        if len(partes) != 2: raise ValueError
        
        inicio = int(partes[0], 16)
        fim = int(partes[1], 16)
        
        escolha = Prompt.ask("Definir % específica?", choices=["s", "n"], default="n")
        
        novo_inicio = 0
        info = ""
        
        if escolha == 's':
            porcentagem = float(Prompt.ask("Qual a porcentagem? (ex: 50.5)").replace(',', '.'))
            offset = int((fim - inicio) * (porcentagem / 100.0))
            novo_inicio = inicio + offset
            info = f"Corte exato em {porcentagem}%"
        else:
            novo_inicio = random.randint(inicio, fim)
            info = "Corte Aleatório (Random)"

        range_final = f"{hex(novo_inicio)[2:]}:{partes[1]}"
        
        console.print(Panel(f"[bold gold1]{range_final}[/]", title=f"[cyan]{info}[/]", border_style="cyan"))
        
        gerar_comandos_externos(range_final)

    except Exception:
        console.print("[bold red]Erro nos dados. Verifique o formato INICIO:FIM[/]")

def definir_zona_de_busca():
    console.rule("[bold red]Definir Zona de Busca (Sniper)[/]")
    
    range_input = Prompt.ask("Digite o range TOTAL [bold](INICIO:FIM)[/]").strip().lower()
    try:
        partes = range_input.split(':')
        base_inicio = int(partes[0], 16)
        base_fim = int(partes[1], 16)
        total = base_fim - base_inicio

        start_pct = float(Prompt.ask("Começar em qual %?").replace(',', '.'))
        size_pct = float(Prompt.ask("Tamanho da janela (%)?").replace(',', '.'))

        offset = int(total * (start_pct / 100.0))
        tamanho = int(total * (size_pct / 100.0))
        
        novo_inicio = base_inicio + offset
        novo_fim = min(novo_inicio + tamanho, base_fim)
        
        range_final = f"{hex(novo_inicio)[2:]}:{hex(novo_fim)[2:]}"

        console.print(Panel(
            f"Início: {start_pct}%\nTamanho: {size_pct}%\n\n[bold gold1]{range_final}[/]",
            title="Zona Definida",
            border_style="red"
        ))
        
        gerar_comandos_externos(range_final)

    except Exception:
        console.print("[bold red]Erro no cálculo. Verifique os números.[/]")

# --- MAIN ---

def main():
    while True:
        console.clear()
        
        # Cabeçalho Bonito
        console.print(Panel.fit(
            "[bold yellow]Ferramenta de Caça Bitcoin[/] v4.0 [italic](Rich Edition)[/]",
            subtitle="Por: [cyan]Gemini & Você[/]",
            border_style="yellow"
        ))

        # Menu
        menu = Table(show_header=False, box=box.SIMPLE)
        menu.add_row("[bold cyan]1.[/] Gerar chave por número", "[dim]Verifica saldo[/]")
        menu.add_row("[bold cyan]2.[/] Gerar chaves em intervalo", "[dim]Loop sequencial[/]")
        menu.add_row("[bold cyan]3.[/] Converter chave", "[dim]WIF/Hex -> Endereço[/]")
        menu.add_row("[bold cyan]4.[/] Calculadora de Range", "[dim]Corte simples[/]")
        menu.add_row("[bold cyan]5.[/] Zona de Busca", "[dim]Início + Tamanho[/]")
        menu.add_row("[bold red]6.[/] Sair", "")
        
        console.print(menu)
        console.print()

        opcao = Prompt.ask("[bold]Escolha uma opção[/]", choices=["1", "2", "3", "4", "5", "6"])

        if opcao == '1':
            try:
                num = int(Prompt.ask("Digite o [bold]número decimal[/]"))
                gerar_chave(num)
                Prompt.ask("\n[dim]Pressione Enter para voltar...[/]")
            except:
                console.print("[red]Número inválido![/]")
                time.sleep(1)

        elif opcao == '2':
            try:
                ini = int(Prompt.ask("Inicio (Decimal)"))
                fim = int(Prompt.ask("Fim (Decimal)"))
                console.print("[yellow]Pressione CTRL+C para parar o loop...[/]")
                time.sleep(1)
                for n in range(ini, fim + 1):
                    gerar_chave(n)
                Prompt.ask("\n[dim]Enter para voltar...[/]")
            except:
                console.print("[red]Inválido![/]")

        elif opcao == '3':
            converter_chave()
            Prompt.ask("\n[dim]Enter para voltar...[/]")

        elif opcao == '4':
            calculadora_range_inteligente()
            Prompt.ask("\n[dim]Enter para voltar...[/]")

        elif opcao == '5':
            definir_zona_de_busca()
            Prompt.ask("\n[dim]Enter para voltar...[/]")

        elif opcao == '6':
            console.print("[bold yellow]Boa caçada! Até mais.[/]")
            break

if __name__ == "__main__":
    # Verifica se as libs estao instaladas antes de rodar
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Programa interrompido pelo usuário.[/]")
    except Exception as e:
        console.print(f"[bold red]Erro fatal:[/ {e}")
