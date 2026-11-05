"""Gera os assets e monta o jogo num único HTML (imagens embutidas como data URI).

Uso:  python3 montar_jogo.py   ->  index.html
"""
import base64, os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
subprocess.run([sys.executable, os.path.join(AQUI, "gerar_assets.py")], check=True)
subprocess.run([sys.executable, os.path.join(AQUI, "gerar_personagens_anime.py")], check=True)

def data_uri(nome):
    with open(os.path.join(AQUI, "rpg_assets_amostra", nome), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()

with open(os.path.join(AQUI, "jogo", "template.html"), encoding="utf-8") as f:
    html = f.read()
for chave, arq in {"__TILESET__": "tileset_terreno.png", "__PROPS__": "props.png", "__SLIMES__": "slimes_128.png", "__VILLAGE__": "vila.png",
                   "__INTERIOR__": "interior_tiles.png", "__MOVEIS__": "moveis.png", "__HEROES128__": "herois_128.png", "__NPCS128__": "npcs_128.png"}.items():
    html = html.replace(chave, data_uri(arq))
with open(os.path.join(AQUI, "index.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("ok -> index.html")
