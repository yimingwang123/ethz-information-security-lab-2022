#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>


char* get_password(char* argv[], FILE* file) {
    char *password = malloc(16);
    int ch;
    for (int i = 0; (ch=getc(file)) != EOF && i<15;){
        password[i] = ch;
        i = i+1;
    }
    return password;
}

int get_correct_amount(char* password) {
    int correct_amount = 0;
    for (int i = 0; i < strlen(password); i++){
        int password_not_dollar = password[i] != '$';
        correct_amount = correct_amount + password_not_dollar;
    }
    return correct_amount;
}

int check_guess(char* argv[], char* password) {
    int is_guess_correct = 1;
    for (int i=0; i<strlen(argv[1]); i++){
        int check_arg = argv[1][i] == password[i + 15 - strlen(argv[1])];
        is_guess_correct = is_guess_correct * check_arg;
    }
    return is_guess_correct;
}

void create_output_file(char* argv[], int correct_amount, int is_guess_correct){
    FILE* output_file;
    output_file = fopen (argv[2], "wb");
    int output = (is_guess_correct == 1) & (correct_amount == strlen(argv[1]));
    fputc(output, output_file);
    fclose(output_file);
}

int main (int argc, char* argv[]) {

    FILE* file;
    file = fopen ("/home/isl/t2_3/password.txt", "r");

    if (file == NULL) {
    perror("The password file does not exist! \n");
    exit(2);
    }

    char* password = get_password(argv, file);
    int correct_amount = get_correct_amount(password);
    int is_guess_correct = check_guess(argv, password);
    create_output_file(argv, correct_amount, is_guess_correct);
    
    fclose(file);
    return 0;
}
