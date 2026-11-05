# Zero Class

Pequeno RPG 2D top-down no estilo JRPG clássico, sem classes de personagem.
O grupo (Lia, Davi e Nina) explora o Campo de Verdelume e enfrenta slimes em
batalhas de tempo ativo (ATB).

Todo o jogo é um único arquivo HTML, sem dependências: abra `index.html` no navegador.

## Controles

| Tecla | Ação |
|---|---|
| Setas / WASD | andar e navegar nos menus |
| Z / Enter / Espaço | confirmar, falar, interagir |
| X / Esc | voltar, abrir o menu de itens |

No celular aparecem botões na tela.

## Como funciona

- **Campo**: lago, estrada, árvores, baús e um santuário com cristal que restaura HP/MP e salva o jogo.
- **Encontros aleatórios**: frequentes na grama alta, raros na estrada, nenhum no santuário.
- **Batalha ATB**: Atacar, Magia (Fogo, Gelo, Cura e Raio a partir do nível 3), Item, Defender e Fugir.
- **Slimes**: Verde (básico), Azul (fraco contra Raio) e Rubro (fraco contra Gelo).
- **Música e efeitos** sintetizados no navegador (Web Audio), com composições originais.
- O progresso fica salvo no `localStorage` do navegador.

## Assets

Todos os gráficos são gerados por código, com paleta fixa e contorno de 1px, em
`rpg_assets_amostra/` (veja `assets.json` para as coordenadas de cada sprite).

| Script | Gera |
|---|---|
| `gerar_assets.py` | tileset de terreno (32×32), props, vila, interiores, paleta |
| `gerar_personagens_anime.py` | heróis e NPCs em 128×128 no estilo JRPG/anime, mais os slimes (usados no jogo) |
| `gerar_personagens128.py` | versão anterior dos personagens 128×128; fornece o acabamento e os slimes |
| `gerar_personagens64.py` | versões 64×64 dos heróis e slimes (não usadas no jogo) |
| `montar_jogo.py` | roda os geradores e embute as imagens em `index.html` |

O jogo desenha o mundo em 480×320 lógicos e a tela em 960×640, então os sprites
de 128×128 aparecem num quadro de 64 com todos os pixels de detalhe.

## Reconstruir

Requer Python 3 com Pillow.

```bash
python3 montar_jogo.py
```

O código do jogo fica em `jogo/template.html`. `jogo/template_com_vila.html` guarda
a versão anterior com a vila e o interior das casas, removidos por enquanto.
