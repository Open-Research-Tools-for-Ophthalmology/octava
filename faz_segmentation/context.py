"""
Holds the context for segmentation
Stores configuration, displayer, runtime flags
"""
from dataclasses import dataclass

# Used so configuration, displayer, and runtime flags can
# be passed around to different modules/functions once instead
# of passing each value as a parameter to every function

# fields are immutable once initialised
@dataclass(frozen=True)
class Context:
    config: dict
    display: object = None
    filename: str = ""
    steps: bool = False
    candidate: bool = False

    def show(self, img, msg=None, final=False):
        """
        Show an image if display is initialised.
        """
        if self.steps and self.display is not None:
            self.display.next_step(img, msg, final)
