from typing import Any, Dict, TypedDict, Union


class playInfo(TypedDict):
    """Information about the state of the machine."""

    isActive: bool
    isCompleted: bool


class Machine:
    """
    Represents an HTB (Hack The Box) machine.

    Attributes:
        id (int): The ID of the machine.
        name (str): The name of the machine.
        os (str): The operating system of the machine.
        release (str): The release date of the machine.
        isTodo (bool): Whether the machine is marked as "To Do".
        difficultyText (str): The difficulty level of the machine.
        star (float): The rating of the machine.
        playInfo (playInfo): Information about the state of the machine.
        authUserInUserOwns (bool): Whether user owns the user flag.
        authUserInRootOwns (bool): Whether user owns the root flag.
        avatar (str): The avatar image URL or path for the machine.
    """

    def __init__(
        self,
        id: int,
        name: str,
        os: str,
        release: str,
        isTodo: bool,
        difficultyText: str,
        star: float,
        playInfo: playInfo,
        authUserInUserOwns: bool,
        authUserInRootOwns: bool,
        avatar: str,
    ):
        """
        Initializes a new instance of the Machine class.

        Parameters:
            id (int): The ID of the machine.
            name (str): The name of the machine.
            os (str): The operating system of the machine.
            release (str): The release date of the machine.
            isTodo (bool): Whether the machine is marked as "To Do".
            difficultyText (str): The difficulty level of the machine.
            star (float): The rating of the machine.
            playInfo (playInfo): Information about the state of the machine.
            authUserInUserOwns (bool): Whether user owns the user flag.
            authUserInRootOwns (bool): Whether user owns the root flag.
            avatar (str): The avatar image URL or path for the machine.
        """

        self.id = id
        self.name = name
        self.os = os
        self.release = release
        self.isTodo = isTodo
        self.difficultyText = difficultyText
        self.star = star
        self.playInfo = playInfo
        self.authUserInUserOwns = authUserInUserOwns
        self.authUserInRootOwns = authUserInRootOwns
        self.avatar = avatar

    def to_dict(self) -> Dict[str, Union[Any, playInfo]]:
        """Convert the Machine object to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "os": self.os,
            "release": self.release,
            "isTodo": self.isTodo,
            "difficultyText": self.difficultyText,
            "star": self.star,
            "playInfo": self.playInfo,
            "authUserInUserOwns": self.authUserInUserOwns,
            "authUserInRootOwns": self.authUserInRootOwns,
            "avatar": self.avatar,
        }
