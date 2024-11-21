#! usr/bin/env python3

# module imports
import argparse
import sys

programName = "parse"
programUsage = "%(prog)s [parsing type] [function]?" # I use prog here and not "programName", because we need it to refer to the variable initiated through the class, not the definition of it
programDesc = "A script to parse fasta files"
programEpilog = "example: %(prog)s file.fna -r --seq-find GC"

class FastaParser(argparse.ArgumentParser):

    def __init__(self, prog = None, usage = None, description = None, epilog = None, parents = [], formatter_class = argparse.HelpFormatter, prefix_chars = "-", fromfile_prefix_chars = None, argument_default = None, conflict_handler = "error", add_help = True, allow_abbrev = True, exit_on_error = False):
        super().__init__(prog, usage, description, epilog, parents, formatter_class, prefix_chars, fromfile_prefix_chars, argument_default, conflict_handler, add_help, allow_abbrev, exit_on_error) # initialise the parent class being called

        # initialise argparser parameters
        self.prog = prog
        self.usage = usage
        self.description = description
        self.epilog = epilog

        parsing_types = self.add_argument_group("Parsing options", "Options for parsing a fasta file")
        parsing_types.add_argument("-r", type=argparse.FileType("r"), nargs=1, help="Read a file (default)")
        parsing_types.add_argument("-w", type=argparse.FileType("+"), nargs=1, help="Read a file and write to it")
        parsing_types.add_argument("-c", type=argparse.FileType("x"), nargs=1, metavar=("W"), help="Create a new file")
        parsing_types.add_argument("-d", type=argparse.FileType("r"), nargs=1, help="display the file")


        functions = self.add_argument_group("Functions", "Functions to do something with parsed data")
        functions.add_argument("--seq-length", type=int, nargs=1, dest="length", help="Find the length of a given sequence (0 for all sequences, positive integer for a singular sequence and a negative integer for sequences up to X)")
        functions.add_argument("--seq-amount", action="store_true", dest="amount", help="Find the amount of sequences")
        functions.add_argument("--seq-starts-with", type=str, nargs=1, dest="starts_with", help="Check if a sequence starts with a given character")
        functions.add_argument("--seq-find", type=str, nargs="+", dest="find", help="Find the occurences of specific strings")
        functions.add_argument("--seq-find-percentage", nargs=1, dest="find_percentage", metavar="FIND", help="Find the occurences (in %%) of specific strings")

        self.args = self.parse_args()
        self.handle_args(self.args)
    
    def handle_args(self, args):
        print(args, "args", sys.argv, "sys args")
        if args.r:

            print("read mode")
            sequences = self.parse_file(args.r[0])

            if args.amount:
                print(len(sequences))
            elif args.starts_with:
                data = self.find_char(args, sequences, args.starts_with[0].upper())
            elif args.find:
                data = self.find_char(args, sequences, args.find)
            elif args.find_percentage:
                data = self.find_char(args, sequences, args.find_percentage[0].upper())  

        if args.w:
            print("readwrite mode")
        if args.c:
            try:
                with open(args.c[0].name, "w+") as newfile:
                    if isinstance(data, list):
                        newfile.writelines(data)
                print("successfully wrote data to new file:", args.c[0].name)
            except FileExistsError:
                print("File already exists")
            except Exception as error:
                print("Error writing to file:", error)
                        
        if args.d:
            sequences = self.parse_file(args.d[0])
            print(sequences)

    
    def parse_file(self, arg) -> list[dict]:
            
            header = ""
            body = ""

            sequences = []

            with arg as file: # with "i" as "x" ensures that whatever file we're accessing, is only being accessed within the block, and is closed after - it is best practice for resource managment
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

                    if header!= "" and body != "":
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

if __name__ == "__main__": # ensure the file runs as a script
    FastaParser(prog=programName, usage=programUsage, description=programDesc, epilog=programEpilog) # create the the command line interactions
    