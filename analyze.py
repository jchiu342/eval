import json
import subprocess
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pickle
import random

import argparse
import time
import io
import threading
import os
import sys
from collections import defaultdict

KATA_PATH = "/mnt/c/Users/wtasf/OneDrive/Documents/go/engines/kata-trt/katago-v1.13.1-trt8.5-cuda11.2-windows-x64"
KWINPATH = "C:/Users/wtasf/OneDrive/Documents/go/engines/kata-trt/katago-v1.13.1-trt8.5-cuda11.2-windows-x64"
KATA_WEIGHTS = "b18net.bin.gz"
KATA_CFG = "analysis_example.cfg"
SAVE_PATH = "analysis/eval.pkl"


if os.path.exists(SAVE_PATH):
    game_evals = pickle.load(open(SAVE_PATH, "rb"))
else:
    game_evals = {}


class Game:
    _col_map = {
        k: v for k, v in zip(list("abcdefghijklmnopqrs"), list("ABCDEFGHJKLMNOPQRST"))
    }
    _row_map = {
        k: v
        for k, v in zip(
            list("abcdefghijklmnopqrs"), [str(i) for i in reversed(range(1, 19 + 1))]
        )
    }

    def __init__(self, name: str, sgf: str):
        """
        Takes sgf strings and returns objects that can easily be converted to
        queries for Kata
        """
        self.list = Game.parse_sgf(sgf, convert_moves=True)
        self.name = name
        self.komi = 0
        self.rule = "japanese"
        self.boardsize = 19

        br = None
        for k, v in self.list:
            if k == "KM":
                self.komi = int(v)
            elif k == "RU":
                self.rule = v.lower()
            elif k == "SZ":
                self.boardsize = int(v)
                if self.boardsize != 19:
                    raise ValueError
            # filter out handicap games
            elif k == "HA":
                if v != "0":
                    raise ValueError

        self.moves = list()
        for k, v in self.list:
            if k in ("B", "W"):
                self.moves.append([k, v])

        # SGFs are missing komi; use default Fox Go Server value
        self.komi = 7.5

    def to_query(self, move: int, search=True):
        """
        If search is True, then asks KataGo to find the best move. Otherwise this function
        asks KataGo to evaluate the player's next move.
        """
        s = "S" if search else "E"
        Q = {
            "id": self.name + f"_{s}_{move}",
            "moves": self.moves[:move],
            "komi": self.komi,
            "boardXSize": self.boardsize,
            "boardYSize": self.boardsize,
            "rules": self.rule,
        }
        if not search:
            Q["allowMoves"] = [
                {
                    "player": self.moves[move][0],
                    "moves": [self.moves[move][1]],
                    "untilDepth": 9000,
                }
            ]

        return Q

    @staticmethod
    def convert_move(s: str):
        c, r = s[0], s[1]
        return Game._col_map[c] + Game._row_map[r]

    @staticmethod
    def parse_sgf(s: str, convert_moves=True) -> list:
        mode = "key"
        k = ""
        v = ""
        L = list()
        last_move = "W"
        for char in s:
            if char in "(); \t\n":
                continue
            elif char == "[":
                mode = "val"
            elif char == "]":
                mode = "key"
                L.append((k, v))
                k = ""
                v = ""
            elif mode == "key":
                k = k + char
            elif mode == "val":
                v = v + char
            else:
                raise Exception(
                    f"Encountered unknown mode-key-val-char combination: {mode} {key} {val} {char}"
                )

        if convert_moves:
            for i, (k, v) in enumerate(L):
                if k in ("B", "W"):
                    L[i] = (k, Game.convert_move(v))
                    if k == last_move:
                        raise ValueError
                    last_move = "B" if last_move == "W" else "W"

        return L


def analyze_games(game_dir, game_evals, num_games):

    proc = subprocess.Popen(
        [
            f"{KATA_PATH}/katago.exe",
            "analysis",
            "-model",
            f"{KWINPATH}/{KATA_WEIGHTS}",
            "-config",
            f"{KWINPATH}/{KATA_CFG}",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True,
    )
    L = list()

    listdir = os.listdir(game_dir)
    random.shuffle(listdir)
    num_responses = 0
    for file in listdir:
        if num_games == 0:
            break
        idx = file.split(".")[0]
        if idx in game_evals.keys():
            continue
        game_evals[idx] = {}
        path_to_sgf = game_dir + "/" + file
        print(f"Analyzing {path_to_sgf}")
        try:
            with open(path_to_sgf, "r", encoding="ISO-8859-1") as f:
                sgf = f.read()
                name = path_to_sgf
            game = Game(name=name, sgf=sgf)
        except ValueError:
            print("Game invalid; skipping")
            continue

        num_games -= 1

        if game.komi not in [6.5, 7.5]:
            raise ValueError

        pos = random.randint(5, len(game.moves) - 1)
        query = {
            "id": idx,
            "moves": game.moves,
            "rules": game.rule,
            "komi": game.komi,
            "boardXSize": 19,
            "boardYSize": 19,
            "analyzeTurns": list(filter(lambda x: x < len(game.moves), [pos])),
            "maxVisits": 200,
        }
        num_responses += len(query["analyzeTurns"])

        proc.stdin.write(f"{json.dumps(query)}\n")
        proc.stdin.flush()

    for _ in range(num_responses):
        raw_out = proc.stdout.readline()
        json_output = json.loads(raw_out)
        try:
            game_evals[json_output["id"]][json_output["turnNumber"]] = json_output[
                "rootInfo"
            ]
        except KeyError:
            break
    proc.kill()
    return game_evals


def analyze_all(game_dir, game_evals=None):
    if game_evals is None:
        game_evals = {}
    while len(game_evals) < len(os.listdir(game_dir)):
        game_evals = analyze_games(game_dir, game_evals, 100)
    return game_evals


if __name__ == "__main__":
    game_evals = {}
    z = analyze_games("db", game_evals, 50)
    pickle.dump(z, open("move_evals.pkl", "wb"))
