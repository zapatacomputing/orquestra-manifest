"""Module to assist with text tables"""
from clint.textui import colored


class Tabler:
    """Tabler makes tables from list(dict) of data.

    * It lets you print multi-sized tables that are readable.
    * Make sure the first line has all the required data fields.
      => Extra data will be ignore in subsequent lines!
    * Data looks like this:

    [
        {
            name: Bob,
            age: young,
            appearance: lovely,
            food: caviar,
        },
        {
            name: Yao,
            age: young,
            appearance: lovely,
            food: caviar,
        }
    ]
    """

    def __init__(self):
        self.data = []

    def get_headings(self):
        """Get headings of data"""
        return list(self.data[0].keys())

    def push_datum(self, **datum):
        """Push a datum on self.data"""
        thing = dict(**datum)
        self.data.append(thing)

    def get_dimensions(self):
        """Get the dimension of data entries, based on first data[0]"""
        dimension = []
        for field in self.data[0]:
            # Use the heading and the data entries to calculate size.
            strings = list([field])
            strings.extend([x.get(field) for x in self.data])
            length = len(max(strings, key=len))
            dimension.append(length)
        return dimension

    def liner(self):
        """Make a seperator line"""
        dims = self.get_dimensions()
        liner = '+'
        for dim in dims:
            liner += f'-{"-" *  dim }-+'
        liner += '\n'
        return liner

    def header(self):
        """Make a header line"""
        dims = self.get_dimensions()
        headings = self.get_headings()
        header = '|'
        for idx, head in enumerate(headings):
            header += f' {head:{dims[idx]}s} |'
        header += '\n'
        return header

    def color_word(self, color, word, output):
        """Make a word red in output"""
        if color == 'red':
            return output.replace(word, str(colored.red(word)))
        elif color == 'green':
            return output.replace(word, str(colored.green(word)))
        elif color == 'blue':
            return output.replace(word, str(colored.blue(word)))
        elif color == 'yellow':
            return output.replace(word, str(colored.yellow(word)))

    def data_lines(self):
        """Return the data in lines"""
        dims = self.get_dimensions()
        headings = self.get_headings()
        output = str()

        for _datum in self.data:
            data_line = '|'
            for idx, _ in enumerate(headings):
                data_line += f' {_datum.get(headings[idx]):{dims[idx]}s} |'
            data_line += '\n'
            output += data_line

        output = self.color_word('red', 'Missing', output)
        output = self.color_word('red', 'None', output)
        output = self.color_word('red', 'Invalid', output)
        output = self.color_word('red', 'N/A', output)
        output = self.color_word('blue', 'Updated', output)
        output = self.color_word('green', 'OK', output)
        output = self.color_word('blue', 'New', output)

        return output

    def get_table(self):
        """Get the table of data"""
        output = self.liner()
        output += self.header()
        output += self.liner()
        output += self.data_lines()
        output += self.liner()
        return output



