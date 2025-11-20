"""
Display class for verbose step by step displaying, used with --steps arg
"""
import matplotlib.pyplot as plt

class Display:
    font = {'family': 'Times New Roman',
    'color':  'purple',
    'weight': 'bold',
    'size': 16
    }

    def __init__(self, original_img):
        self.original = original_img.copy()
        self.previous = None
        self.current = None
        self.step = 0

    def next_step(self, image, msg=None, final=False):
        self.step += 1

        if self.step == 1:
            self.current = image.copy()
        else:
            self.previous = self.current.copy()
            self.current = image.copy()

        self.display_step(msg, final=final)

    def display_step(self, msg=None, final=False):
        plt.figure(figsize=(12, 5))

        step_str = f'step {str(self.step)}: '

        plt.subplot(131), plt.imshow(self.original, cmap='gray')
        plt.title('Input Image'), plt.xticks([]), plt.yticks([])

        # step 1 has no 'previous'
        if self.step > 1:
            plt.subplot(132), plt.imshow(self.previous, cmap='gray')
            plt.title('Previous Step'), plt.xticks([]), plt.yticks([])
            plt.subplot(133), plt.imshow(self.current, cmap='gray')
            plt.title('Current Step'), plt.xticks([]), plt.yticks([])
        else:
            plt.subplot(132), plt.imshow(self.current, cmap='gray')
            plt.title('Current Step'), plt.xticks([]), plt.yticks([])

        plt.tight_layout()

        plt.subplots_adjust(top=0.85)

        if final:
            plt.figtext(0.5, 0.95, "Final Processed",
                horizontalalignment='center', verticalalignment='top', fontdict=self.font)
        else:
            plt.figtext(0.5, 0.95, step_str + msg,
                horizontalalignment='center', verticalalignment='top', fontdict=self.font)
        
        plt.show()

    