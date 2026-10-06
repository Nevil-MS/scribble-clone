from dataclasses import dataclass
from typing import Any


@dataclass
class ClientMessage:
    type: str
    data: dict[str, Any]

    @classmethod
    def from_dict(cls, message: dict[str, Any]) -> "ClientMessage":
        if not isinstance(message, dict):
            return cls(type="", data={})

        data = message.get("data", {})
        if not isinstance(data, dict):
            data = {}

        return cls(
            type=str(message.get("type", "")),
            data=data,
        )


@dataclass
class ServerMessage:
    type: str
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "data": self.data,
        }


def error_message(message: str) -> dict[str, Any]:
    return ServerMessage(
        type="error",
        data={"message": message},
    ).to_dict()


def system_message(message: str) -> dict[str, Any]:
    return ServerMessage(
        type="system_message",
        data={"message": message},
    ).to_dict()


def chat_message(pid: str, name: str, message: str) -> dict[str, Any]:
    return ServerMessage(
        type="chat",
        data={
            "pid": pid,
            "name": name,
            "message": message,
        },
    ).to_dict()


def player_joined(player: dict[str, Any]) -> dict[str, Any]:
    return ServerMessage(
        type="player_joined",
        data={"player": player},
    ).to_dict()


def player_left(pid: str) -> dict[str, Any]:
    return ServerMessage(
        type="player_left",
        data={"pid": pid},
    ).to_dict()


def game_state_message(state: str) -> dict[str, Any]:
    return ServerMessage(
        type="game_state",
        data={"state": state},
    ).to_dict()


def word_options_message(options: list[dict[str, Any]]) -> dict[str, Any]:
    return ServerMessage(
        type="word_options",
        data={"options": options},
    ).to_dict()


def timer_message(seconds: int, phase: str) -> dict[str, Any]:
    return ServerMessage(
        type="timer",
        data={
            "seconds": max(0, int(seconds)),
            "phase": phase,
        },
    ).to_dict()


def leaderboard_message(players: list[dict[str, Any]]) -> dict[str, Any]:
    return ServerMessage(
        type="leaderboard",
        data={"players": players},
    ).to_dict()

