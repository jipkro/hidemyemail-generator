# Function to remove empty lines from a file
def remove_empty_lines(input_file, output_file):
    with open(input_file, 'r') as infile:
        lines = infile.readlines()
        
    # Filter out empty lines
    cleaned_lines = [line for line in lines if line.strip()]

    with open(output_file, 'w') as outfile:
        outfile.writelines(cleaned_lines)

if __name__ == "__main__":
    input_file = 'emails.txt'
    output_file = 'cleaned_emails.txt'
    remove_empty_lines(input_file, output_file)
    print(f"Cleaned emails have been saved to {output_file}")