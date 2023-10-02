from typing import Any, Dict, TypedDict, Union


class MachineState(TypedDict):
    """Information about the state of the machine."""

    isActive: bool
    isCompleted: bool


class Machine:
    """
    Represents an HTB (Hack The Box) machine.

    Attributes:
        machine_id (int): The ID of the machine.
        name (str): The name of the machine.
        os (str): The operating system of the machine.
        release_date (str): The release date of the machine.
        todo (bool): Whether the machine is marked as "To Do".
        difficulty (str): The difficulty level of the machine.
        rating (float): The rating of the machine.
        machine_state (MachineState): Information about the state of the machine.
        authUserInUserOwns (bool): Whether user owns the user flag.
        authUserInRootOwns (bool): Whether user owns the root flag.
        image (str): The avatar image URL or path for the machine.
    """

    def __init__(
        self,
        machine_id: int,
        name: str,
        os: str,
        release_date: str,
        todo: bool,
        difficulty: str,
        rating: float,
        machine_state: MachineState,
        userOwned: bool,
        rootOwned: bool,
        image: str,
    ):
        """
        Initializes a new instance of the Machine class.

        Parameters:
            machine_id (int): The ID of the machine.
            name (str): The name of the machine.
            os (str): The operating system of the machine.
            release_date (str): The release date of the machine.
            todo (bool): Whether the machine is marked as "To Do".
            difficulty (str): The difficulty level of the machine.
            rating (float): The rating of the machine.
            machine_state (MachineState): Information about the state of the machine.
            authUserInUserOwns (bool): Whether user owns the user flag.
            authUserInRootOwns (bool): Whether user owns the root flag.
            image (str): The avatar image URL or path for the machine.
        """

        self.id = machine_id
        self.name = name
        self.os = os
        self.release_date = release_date
        self.todo = todo
        self.difficulty = difficulty
        self.rating = rating
        self.machine_state = machine_state
        self.userOwned = userOwned
        self.rootOwned = rootOwned
        self.image = image

    def to_dict(self) -> Dict[str, Union[Any, MachineState]]:
        """Convert the Machine object to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "os": self.os,
            "release": self.release_date,
            "isTodo": self.todo,
            "difficultyText": self.difficulty,
            "star": self.rating,
            "playInfo": self.machine_state,
            "authUserInUserOwns": self.userOwned,
            "authUserInRootOwns": self.rootOwned,
            "avatar": self.image,
        }
