import atheris
import sys


# The function we want to fuzz
@atheris.instrument_func
def process_input(data):
    if len(data) < 3:
        return
    if data[0] == "b":
        if data[1] == "u":
            if data[2] == "g":
                raise ValueError("Bug found!")  # Simulate a bug


# Fuzz driver function


@atheris.instrument_func
def fuzz_input(data):
    # Convert the input bytes to a string
    try:
        decoded_data = data.decode("utf-8")
    except UnicodeDecodeError:
        return  # Skip invalid UTF-8 inputs

    # Call the function to fuzz
    process_input(decoded_data)


# Main function to set up and run the fuzzer
def main():
    # Set up the fuzzer
    atheris.Setup(sys.argv, fuzz_input)

    # Start fuzzing
    atheris.Fuzz()


if __name__ == "__main__":
    main()
