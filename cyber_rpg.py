#!/usr/bin/env python3
# cyber_rpg.py
# Mini text-based Cyberpunk Hacker RPG - Ju Edition
# Roda no terminal. Python 3.7+

import random
import time
import os
import sys
from datetime import datetime

# -------------------------
# Configurações / constantes
# -------------------------
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

SCORES_FILE = "scores.txt"

# XP required per level (simple formula)
def xp_for_level(lv):
    return 50 + (lv - 1) * 50

# -------------------------
# Utils
# -------------------------
def slow_print(text, delay=0.01):
    for c in text:
        print(c, end="", flush=True)
        time.sleep(delay)
    print()

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def clamp(v, a, b):
    return max(a, min(b, v))

# -------------------------
# Player / Enemy classes
# -------------------------
class Actor:
    def __init__(self, name, hp_max, attack, defense, crit=0.05):
        self.name = name
        self.hp_max = hp_max
        self.hp = hp_max
        self.attack = attack
        self.defense = defense
        self.crit = crit  # chance
        self.alive = True

    def take_damage(self, dmg):
        dmg = max(0, int(dmg))
        self.hp -= dmg
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return dmg

    def heal(self, amount):
        self.hp = clamp(self.hp + amount, 0, self.hp_max)

    def is_alive(self):
        return self.alive and self.hp > 0

class Player(Actor):
    def __init__(self, handle, cls):
        # base by class
        if cls == "Infiltrador":
            super().__init__(handle, hp_max=90, attack=18, defense=6, crit=0.12)
        elif cls == "Engenheiro":
            super().__init__(handle, hp_max=120, attack=12, defense=10, crit=0.06)
        elif cls == "Analista":
            super().__init__(handle, hp_max=100, attack=14, defense=8, crit=0.15)
        else:
            super().__init__(handle, hp_max=100, attack=14, defense=8, crit=0.08)

        self.cls = cls
        self.level = 1
        self.xp = 0
        self.xp_next = xp_for_level(self.level)
        self.items = {"Patch": 2, "Overclock": 1, "Proxy": 1}
        self.buff_attack = 0
        self.buff_turns = 0
        self.games_played = 0

    def gain_xp(self, amount):
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_next:
            self.xp -= self.xp_next
            self.level_up()
            leveled = True
        return leveled

    def level_up(self):
        self.level += 1
        self.xp_next = xp_for_level(self.level)
        # scale up stats
        self.hp_max += 10
        self.attack += 2
        self.defense += 1
        self.hp = self.hp_max  # heal on level
        slow_print(f"{CYAN}~ LEVEL UP! Agora você é nível {self.level}. Stats aumentados!{RESET}", 0.005)

    def effective_attack(self):
        return self.attack + self.buff_attack

    def tick_buffs(self):
        if self.buff_turns > 0:
            self.buff_turns -= 1
            if self.buff_turns == 0:
                self.buff_attack = 0

# -------------------------
# Enemy generation
# -------------------------
def make_enemy(danger=1, rng=None):
    if rng is None:
        rng = random
    # danger scales strength and hp
    enemy_types = [
        ("Minor Firewall", 60, 10, 4, 0.03, 20),
        ("Black ICE", 80, 14, 6, 0.05, 35),
        ("Sentinel AI", 100, 18, 8, 0.07, 60),
        ("Trace Hunter", 120, 22, 10, 0.10, 80),
    ]
    name, hp, atk, df, crit, xp = rng.choice(enemy_types)
    # scale with danger
    hp = int(hp * (1 + 0.15 * (danger - 1)))
    atk = int(atk * (1 + 0.12 * (danger - 1)))
    df = int(df * (1 + 0.10 * (danger - 1)))
    xp = int(xp * (1 + 0.20 * (danger - 1)))
    enemy = Actor(name, hp, atk, df, crit)
    enemy.xp_reward = xp
    return enemy

# Boss
def make_boss(rng=None):
    if rng is None:
        rng = random
    boss = Actor("Core Security AI (BOSS)", 220, 28, 12, 0.12)
    boss.xp_reward = 200
    return boss

# -------------------------
# Combat system
# -------------------------
def calculate_damage(attacker_attack, defender_defense, crit_chance, rng=None):
    if rng is None:
        rng = random
    base = attacker_attack - int(defender_defense * 0.5)
    base = max(1, base)
    # variance
    variance = rng.uniform(0.85, 1.15)
    dmg = base * variance
    # crit?
    is_crit = rng.random() < crit_chance
    if is_crit:
        dmg *= 1.8
    return int(max(1, dmg)), is_crit

def player_turn(player: Player, enemy: Actor, rng=None):
    if rng is None:
        rng = random
    while True:
        print(f"\n{BOLD}Suas opções:{RESET}")
        print("1) Exploit (Atacar)")
        print("2) Fortify (Aumentar defesa temporária)")
        print("3) Usar item")
        print("4) Fugir")
        choice = input("Escolha [1-4]: ").strip()
        if choice == "1":
            dmg, crit = calculate_damage(player.effective_attack(), enemy.defense, player.crit, rng)
            dealt = enemy.take_damage(dmg)
            if crit:
                slow_print(f"{YELLOW}CRÍTICO!{RESET} Você explodiu uma vulnerabilidade e causou {dealt} de dano.", 0.005)
            else:
                slow_print(f"Você lançou um exploit e causou {dealt} de dano.", 0.005)
            return "attack"
        elif choice == "2":
            # Fortify increases defense for this turn (we'll implement as temporary heal to defense)
            orig_def = player.defense
            player.defense += 6
            slow_print("Você fortaleceu seu firewall pessoal (defesa aumentada por 1 turno).", 0.005)
            return "fortify"
        elif choice == "3":
            if sum(player.items.values()) == 0:
                slow_print("Você não tem itens. Volte quando tiver crachá, quer dizer, itens.", 0.005)
                continue
            use_item(player, rng)
            return "item"
        elif choice == "4":
            # attempt to flee: success chance depends on enemy strength vs player level
            base_chance = 0.45 + (player.level - 1) * 0.03
            # enemy weight
            weight = (enemy.attack + enemy.defense) / 100.0
            chance = clamp(base_chance - weight * 0.1, 0.1, 0.9)
            if rng.random() < chance:
                slow_print(f"{CYAN}Fuga bem-sucedida!{RESET}", 0.005)
                return "fled"
            else:
                slow_print(f"{RED}Fuga falhou!{RESET} O sistema travou sua rota.", 0.005)
                return "failed_flee"
        else:
            print("Escolha inválida. Digita 1-4.")

def use_item(player: Player, rng=None):
    if rng is None:
        rng = random
    while True:
        print("\nItens:")
        for i, (k, v) in enumerate(player.items.items(), 1):
            print(f"{i}) {k} x{v}")
        print(f"{len(player.items)+1}) Voltar")
        choice = input("Usar qual? ").strip()
        try:
            c = int(choice)
        except:
            print("Entrada inválida.")
            continue
        keys = list(player.items.keys())
        if c == len(keys) + 1:
            return
        if 1 <= c <= len(keys):
            item = keys[c-1]
            if player.items[item] <= 0:
                print("Você não tem esse item.")
                continue
            # apply effect
            if item == "Patch":
                heal_amt = int(player.hp_max * 0.35)
                player.heal(heal_amt)
                slow_print(f"Patch aplicado. Você recuperou {heal_amt} HP.", 0.005)
            elif item == "Overclock":
                player.buff_attack = int(player.attack * 0.5)
                player.buff_turns = 3
                slow_print("Overclock ativado: +50% ataque por 3 turnos. Cuidado com o aquecimento.", 0.005)
            elif item == "Proxy":
                # gives an immediate small chance to auto-escape next flee attempt (we can implement as +0.25 flee base)
                slow_print("Proxy ativado: sua próxima tentativa de fuga tem +25% de chance.", 0.005)
                # implement by giving a temporary tag
                player._proxy_active = True
            else:
                slow_print("Item desconhecido... (bug?!)", 0.005)
            player.items[item] -= 1
            return
        else:
            print("Escolha inválida.")

def enemy_turn(player: Player, enemy: Actor, player_action, rng=None):
    if rng is None:
        rng = random
    # enemy simple AI: if low hp, chance to do heavy attack or try to debuff
    if not enemy.is_alive():
        return
    # enemy attack:
    dmg, crit = calculate_damage(enemy.attack, player.defense, enemy.crit, rng)
    # if player fortified previous action, they had extra defense added for that turn - we reset after
    taken = player.take_damage(dmg)
    if crit:
        slow_print(f"{RED}{enemy.name} acertou um golpe crítico e causou {taken} de dano!{RESET}", 0.005)
    else:
        slow_print(f"{enemy.name} atacou e causou {taken} de dano.", 0.005)

# -------------------------
# High-score / saving
# -------------------------
def save_score(handle, score, lvl):
    try:
        with open(SCORES_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} | {handle} | score={score} | level={lvl}\n")
    except Exception:
        pass

# -------------------------
# Game loop & flow
# -------------------------
def choose_class():
    clear()
    slow_print(f"{BOLD}Escolha sua especialização de netrunner:{RESET}\n")
    print("1) Infiltrador — alto dano crítico, frágil em defesa.")
    print("2) Engenheiro  — tanque técnico, mais HP e defesa.")
    print("3) Analista   — crítico alto e ataques mais precisos.")
    while True:
        c = input("Escolha (1-3): ").strip()
        if c == "1":
            return "Infiltrador"
        if c == "2":
            return "Engenheiro"
        if c == "3":
            return "Analista"
        print("Escolha inválida.")

def intro(handle):
    clear()
    slow_print(f"{CYAN}--- CONNECTING TO NEON GRID ---{RESET}\n", 0.002)
    slow_print(f"Bem-vindo, {BOLD}{handle}{RESET}. O sistema pulsa. Você é um netrunner procurando falhas.", 0.01)
    slow_print("Objetivo: invadir nós, coletar XP, melhorar suas skills e derrubar o Core Security AI.\n", 0.01)
    input("Pressione Enter para iniciar sua incursão...")

def battle(player: Player, enemy: Actor, rng=None):
    if rng is None:
        rng = random
    slow_print(f"\n{YELLOW}>>> Confronto: {enemy.name} (HP {enemy.hp}/{enemy.hp_max}){RESET}\n", 0.005)
    escaped = False
    while player.is_alive() and enemy.is_alive():
        # show status
        print(f"{BOLD}{player.name} (Lvl {player.level}) — HP: {player.hp}/{player.hp_max}  |  XP: {player.xp}/{player.xp_next}{RESET}")
        print(f"{enemy.name} — HP: {enemy.hp}/{enemy.hp_max}")
        action = player_turn(player, enemy, rng)
        if action == "attack":
            # already handled printing inside player_turn
            pass
        elif action == "fortify":
            # temporary defense bonus applied inside player_turn (we must ensure enemy attack will consider it)
            pass
        elif action == "item":
            pass
        elif action == "fled":
            escaped = True
            break
        elif action == "failed_flee":
            pass

        if enemy.is_alive():
            enemy_turn(player, enemy, action, rng)
        # tick buffs and remove temporary fortify effect (we added +6 defense directly)
        player.tick_buffs()
        # If player had fortified, reduce the temporary defense back:
        if action == "fortify":
            player.defense = max(0, player.defense - 6)

    if not player.is_alive():
        slow_print(f"{RED}\nVocê foi desconectado... seu avatar se perdeu no Neon Grid.{RESET}\n", 0.005)
        return False, 0  # lost
    if escaped:
        slow_print("Você fugiu do encontro.", 0.005)
        return True, 0  # escaped, no XP
    if not enemy.is_alive():
        slow_print(f"{GREEN}\nInimigo derrubado! XP ganho: {enemy.xp_reward}{RESET}", 0.005)
        return True, enemy.xp_reward

# -------------------------
# Main game
# -------------------------
def main():
    rng = random.Random()
    clear()
    slow_print(f"{BOLD}{CYAN}--- CYBER RPG: NEON RUNNER ---{RESET}\n", 0.004)
    handle = input("Escolha seu handle (nome): ").strip() or "anon"
    cls = choose_class()
    player = Player(handle, cls)
    intro(handle)

    score = 0
    encounters = 0
    difficulty = 1
    # game loop: waves until player dies or defeats boss
    while player.is_alive():
        encounters += 1
        # every 5 encounters, increase difficulty slightly
        if encounters % 5 == 0:
            difficulty += 1
        # every 7 encounters, spawn boss
        if encounters == 7:
            enemy = make_boss(rng)
            slow_print(f"{RED}{BOLD}\n!!! ALERTA: CORE SECURITY AI DETECTADO !!!{RESET}\n", 0.002)
        else:
            enemy = make_enemy(danger=difficulty, rng=rng)
        cont, xp = battle(player, enemy, rng)
        if not cont:
            break
        score += xp
        leveled = player.gain_xp(xp)
        if leveled:
            slow_print(f"{CYAN}Você subiu de nível! HP restaurado.{RESET}")
        # small chance to find an item
        if random.random() < 0.25:
            found = rng.choice(["Patch", "Overclock", "Proxy"])
            player.items[found] = player.items.get(found, 0) + 1
            slow_print(f"{YELLOW}Você garimpou um item: {found}{RESET}", 0.005)
        # win condition: boss defeated
        if enemy.name.startswith("Core Security AI") and not enemy.is_alive():
            slow_print(f"{GREEN}{BOLD}\nPARABÉNS! Você derrotou o Core Security AI e ganhou o Neon Crown!{RESET}\n", 0.003)
            break
        # small rest / shop opportunity
        print("\nDeseja continuar hackeando ou encerrar agora?")
        print("1) Continuar incursão")
        print("2) Encerrar e salvar score")
        resp = input("Escolha [1-2]: ").strip()
        if resp != "1":
            break

    slow_print(f"\n{BOLD}Sessão finalizada. Score total: {score} | Level final: {player.level}{RESET}", 0.005)
    save_score(player.name, score, player.level)
    slow_print("Score salvo. Obrigado por jogar. Volte sempre — mas não seja pego.", 0.002)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrompido. Saindo...")
        sys.exit(0)
