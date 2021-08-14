//
// Created by Andrej Zaujec on 03/04/2021.
//
#include "string"

float friedman_test(std::string input){
    const char * alphabet = "abcdefghijklmnopqrstuvwxyz";
    int alphabetCount = 26;

    std::map<char,int> letterOccurences;

    for (int i = 0; i < alphabetCount; i++){
        char currentLetter = alphabet[i];
        letterOccurences[currentLetter] = std::count(input.begin(), input.end(), currentLetter);
    }

    double sum = 0;
    for(int i = 0; i < alphabetCount; i++) {
        char currentLetter = alphabet[i];
        int letterOccurence = letterOccurences[currentLetter];
        sum += letterOccurence * (letterOccurence - 1);
    }

    double k0 = sum/(input.size() * (input.size() - 1));
    double kp = 0.065;
    double kr = 0.0385 ;

    double result = (kp - kr) / (k0 - kr);
    return result;
}

