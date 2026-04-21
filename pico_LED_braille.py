from machine import Pin

from braille import translate_text


class braille_reader:
    """Drive six pins as one Braille cell from translate_text() output."""

    def __init__(self, pin_list, char_len, line_num=1, text_input=""):
        self.char_len = char_len
        self.line_num = line_num
        self.pin_list = pin_list
        self.cursor = 0
        self.real_text = text_input
        self.braille_text = translate_text(text_input)

        if len(self.braille_text) > 0:
            self.show()

    def __str__(self):
        return str(vars(self))

    def take_input(self, string):
        self.clear()
        self.real_text = string
        self.braille_text = translate_text(string)
        self.cursor = 0
        self.show()

    def show(self):
        if not self.braille_text:
            self.clear()
            return

        if self.cursor < 0 or self.cursor >= len(self.braille_text):
            print("cursor out of range")
            return

        item = self.braille_text[self.cursor]
        pattern = item.get("pattern", "000000")
        pattern = (pattern + "000000")[:6]

        ch = item.get("char", "?")
        print("%s : %s" % (ch, pattern))

        for i in range(6):
            bit = pattern[i]
            pin_val = 1 if bit == "1" else 0
            self.pin_list[i].value(pin_val)

        print(
            "%s %s %s %s %s %s"
            % (
                self.pin_list[0].value(),
                self.pin_list[1].value(),
                self.pin_list[2].value(),
                self.pin_list[3].value(),
                self.pin_list[4].value(),
                self.pin_list[5].value(),
            )
        )

    def move(self, direction):
        # direction is 1 (next) or -1 (previous), step is char_len cells
        try:
            next_cursor = self.cursor + (self.char_len * direction)
            if 0 <= next_cursor < len(self.braille_text):
                self.cursor = next_cursor
                self.show()
        except Exception as e:
            print(e)

    def clear(self):
        for pin in self.pin_list:
            pin.value(0)