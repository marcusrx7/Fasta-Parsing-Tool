#! usr/bin/env python3

# module imports
import argparse
import sys

# Program metadata
programName = "parse"
programUsage = "%(prog)s [parsing type] [function]?" # I use prog here and not "programName", because we need it to refer to the variable initiated through the class, not the definition of it
programDesc = "A script to parse fasta files"
programEpilog = "example: %(prog)s file.fna -r --seq-find GC"

class FastaParser(argparse.ArgumentParser):

    def __init__(self, prog=None, usage=None, description=None, epilog=None, parents=[], formatter_class=argparse.RawTextHelpFormatter, prefix_chars="-", fromfile_prefix_chars=None, argument_default=None, conflict_handler="error", add_help=True, allow_abbrev=False, exit_on_error=False):
        # Initialize the parent class (argparse.ArgumentParser)
        super().__init__(prog, usage, description, epilog, parents, formatter_class, prefix_chars, fromfile_prefix_chars, argument_default, conflict_handler, add_help, allow_abbrev, exit_on_error)

        # Initialize argparser parameters
        self.prog = prog
        self.usage = usage
        self.description = description
        self.epilog = epilog

        # Define argument groups and arguments
        parsing_types = self.add_argument_group("Parsing options", "Options for parsing a fasta file")

        # Mutually exclusive group for required read options
        required_read = parsing_types.add_mutually_exclusive_group(required=True)
        required_read.add_argument("-r", "--read", type=argparse.FileType("r"), nargs=1, help="Read a file (default)")
        required_read.add_argument("-d", "--display", type=argparse.FileType("r"), nargs=1, help="Display the file")

        # Mutually exclusive group for optional write options
        required_write = parsing_types.add_mutually_exclusive_group(required=False)
        required_write.add_argument("-w", "--write", type=argparse.FileType("+"), nargs=1, help="Read a file and write to it")
        required_write.add_argument("-c", "--create", type=argparse.FileType("x"), nargs=1, metavar="W", help="Create a new file and write to it")

        # Define function arguments
        functions = self.add_argument_group("Functions", "Functions to do something with parsed data")
        functions.add_argument("-l", "--length", type=int, nargs=1, dest="length", help="Find the length of a given sequence (0 for all, positive integer to specify a line and a negative integer to specify up to a line)")
        functions.add_argument("-a", "--amount", action="store_true", dest="amount", help="Find the amount of sequences")
        functions.add_argument("-s", "--starts-with", type=str, nargs=1, dest="starts_with", help="Check if a sequence starts with a given character")
        functions.add_argument("-f", "--find", type=str, nargs="+", dest="find", help="Find the occurrences of specific strings")
        functions.add_argument("-fp", "--find-percentage", nargs=1, dest="find_percentage", metavar="FIND", help="Find the occurrences (in %%) of specific strings")
        functions.add_argument("-fl", "--filter", type=str, nargs=1, metavar="FILTER", help="Filter out a given string")
        functions.add_argument("-fr", "--filter-right", type=str, nargs=1, metavar="FILTER", help="Filter out a given string, starting from the right")

        # Parse the arguments and handle them
        self.args = self.parse_args()
        self.handle_args(self.args)

    # Method to handle the parsed arguments
    def handle_args(self, args):
        print(args, "args", sys.argv, "sys args")  # Print the parsed arguments and system arguments for debugging

        if args.read:  # If the read option is selected
            print("read mode")
            sequences = self.parse_file(args.read[0])  # Parse the file

            if args.amount:  # If the amount option is selected
                print(len(sequences))  # Print the number of sequences
            elif args.length:  # If the length option is selected
                index = args.length[0] - 1  # Calculate the index based on the length argument

                if args.length[0] == 0:  # If length is 0, print the length of all sequences
                    for i in sequences:
                        seq = list(i.values())[0]
                        print(list(i.keys())[0], "contains", len(seq), "nucleotides")
                elif args.length[0] > 0:  # If length is positive, print the length of the specified sequence
                    print(list(sequences[index].keys())[0], "contains", len(list(sequences[index].values())[0]), "nucleotides")
                elif args.length[0] < 0:  # If length is negative, print the length of sequences up to the specified index
                    absolute = abs(index)
                    count = 0
                    for i in sequences:
                        count += 1
                        if count < absolute:
                            print(list(i.keys())[0], "contains", len(list(i.values())[0]), "characters")

            elif args.starts_with:  # If the starts-with option is selected
                data = self.find_char(args, sequences, args.starts_with)
            elif args.find:  # If the find option is selected
                data = self.find_char(args, sequences, args.find)
            elif args.find_percentage:  # If the find-percentage option is selected
                data = self.find_char(args, sequences, args.find_percentage)
            elif args.filter or args.filter_right:  # If the filter or filter-right option is selected
                data = self.filter(args, sequences, args.filter)

        if args.write:  # If the write option is selected
            print("readwrite mode")
        if args.create:  # If the create option is selected
            try:
                with open(args.create[0].name, "x") as newfile:  # Open the file in create mode
                    if data:
                        if isinstance(data, list):
                            newfile.writelines(data)  # Write the data to the file
                        else:
                            newfile.write(data)
                print("successfully wrote data to new file:", args.create[0].name)
            except FileExistsError:
                print("File already exists")
            except Exception as error:
                print("Error writing to file:", error)

        if args.display:  # If the display option is selected
            sequences = self.parse_file(args.display[0])
            for i in sequences:
                print("\n" + list(i.keys())[0] + "\n" + list(i.values())[0])

    
    def parse_file(self, arg) -> list[dict]:
            
            header = ""
            body = ""

            sequences = []

            with arg as file: # with "i" as "x" (in this case arg as file) ensures that whatever file we're accessing, is only being accessed within the block, and is closed after - it is best practice for resource managment
                contents: str = file.read().strip()
                lines = contents.split("\n")

            if arg.name.endswith(".faa"):
                for i in lines:
                    line = i.strip("\n")

                    if line.startswith(">"):
                        header = line
                    else:
                        body = line

                    if header!= "" and body != "":
                        seq = {header: body}
                        sequences.append(seq)
                        header = ""
                        body = ""

            elif arg.name.endswith(".fna"):
                count = 0
                for i in lines:
                    count += 1
                    line = i.strip("\n")

                    if line.startswith(">"):
                        header = line
                    else:
                        body = line

                    if body != "":
                        header_line = header + " line " + str(count) + "\n"
                        seq = {header_line: body}
                        sequences.append(seq)
                        body = ""
       
            # Append the last sequence if there is any remaining data
            if header and body:
                seq = {header: body}
                sequences.append(seq)

            return sequences
            
    def find_char(self, arg, sequences: list[dict], chars: list[str]) -> list[str]:
        final_status = []
        result = []
        for i in chars:
            char = i.upper()
            if char:
                if arg.starts_with:
                    count = 0
                    for i in sequences:
                        seq = list(i.values())[0]  # Extract the first value and convert to string
                        if seq.startswith(char):
                            count += 1
                        status = "Successfully found " + str(count) + " sequence(s) starting with: " + char
                        result_line = f"True for {list(i.keys())[0]}"

                    result.append(result_line)       
                    final_status.append(status)

                elif arg.find:
                    total_count = 0
                    total_occurrences = 0
                    for i in sequences:
                        seq = list(i.values())[0]  # Extract the first value and convert to string
                        count = len(seq)
                        occurrences = seq.count(char)
                        percentage = round((occurrences/count) * 100, 3)
                        total_count += count
                        total_occurrences += occurrences
                        result_line = f"{list(i.keys())[0]} contains {char} {occurrences} times as {str(percentage)} % \n"

                        if occurrences:
                            result.append(str(result_line))

                    if total_count > 0:
                        num_occurrences = round((total_occurrences / total_count) * 100, 3)
                        status = "\n (Successfully found " + str(total_occurrences) + " occurrences of: " + char + ")"
                        perc_status= char + " occurs as " + str(num_occurrences) + "%" + " of the total sequences \n"
                    else:
                        status = "\n (Couldn't find any occurrences of: " + char + ")"

                    final_status.append(status)
                    final_status.append(perc_status)

        for i in result:
            print(i)
        for i in final_status:
            print(i)

        return result

    def filter(self, arg, sequences:list[str], chars:list[str]) -> list[str]: # simple method to cut (split) specified strings from the sequences
        result = []
        for c in chars:
            char = c.upper()
            if char:
                for i in sequences:
                    seq = list(i.values())[0]

                    if arg.filter and seq.find(char):
                        cut_seq = seq.split(char)
                    elif arg.filter_right:
                        cut_seq = seq.rsplit(char)        
                        

                    result.append(("".join(cut_seq)+"\n"))

        print(result)
        return result

if __name__ == "__main__": # ensure the file runs as a script
    FastaParser(prog=programName, usage=programUsage, description=programDesc, epilog=programEpilog) # create the the command line interactions using the class
    