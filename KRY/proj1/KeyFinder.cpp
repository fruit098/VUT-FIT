//
// Created by Andrej Zaujec on 03/04/2021.
//

#include "KeyFinder.h"
#include "string"
#include "map"
#include <cmath>
#include "algorithm"

class KeyFinder {
    public:
        std::string input;
        int keyLenght;
        std::map<int, std::string> inputSubstrings;
        const float probability[26] = {
                0.082,
                0.015,
                0.028,
                0.043,
                0.13,
                0.022,
                0.02,
                0.061,
                0.07,
                0.0015,
                0.0077,
                0.04,
                0.024,
                0.067,
                0.075,
                0.019,
                0.00095,
                0.06,
                0.063,
                0.091,
                0.028,
                0.0098,
                0.024,
                0.0015,
                0.02,
                0.00074
        };
        const char * alphabet = "abcdefghijklmnopqrstuvwxyz";
        const int alphabetCount = 26;


    KeyFinder (int keyLenght, std::string input) {
        this->keyLenght = keyLenght;


        this->input = input;
        for (int i = 0; i < keyLenght; i++){
            this->inputSubstrings[i] = std::string ();
        }

        this->splitInputIntoSubstrings();
    }

    void splitInputIntoSubstrings();

    char findLetter(int subString);

    std::string findKey();

    double countCoincidence(int subStringIndex);

    double countAverageCoincidence();
};

void KeyFinder :: splitInputIntoSubstrings (){
    for (int i = 0; i < this->input.size(); i++) {
        int remainder = i % this->keyLenght;
        this->inputSubstrings[remainder].push_back(this->input.at(i));
    }
}

double KeyFinder :: countAverageCoincidence() {
    double sum = 0;
    for (int i = 0; i < this->keyLenght; i++ ){
        sum += countCoincidence(i);
    }
    return sum / this->keyLenght;
}

double KeyFinder :: countCoincidence(int subStringIndex) {
    std::map<char,int> letterOccurences;
    std::string subString = this->inputSubstrings[subStringIndex];

    for (int i = 0; i < this->alphabetCount; i++){
        char currentLetter = this->alphabet[i];
        letterOccurences[currentLetter] = std::count(subString.begin(), subString.end(), currentLetter);
    }

    double sum = 0;
    for (int j = 0; j < this->alphabetCount; j++) {
        char  currentLetter = this->alphabet[j];
        int letterOccurence =letterOccurences[currentLetter];
        sum += (letterOccurence * (letterOccurence - 1));
    }

    return sum/(subString.size() * (subString.size() -1));
}

std::string KeyFinder :: findKey (){
    std::string key;

    for (int i = 0; i < this->keyLenght; i++ ){
        key.push_back(this->findLetter(i));
    }
    return key;
}

char KeyFinder :: findLetter (int subStringIndex){
    std::map<char,int> letterOccurences;
    std::string subString = this->inputSubstrings[subStringIndex];

    for (int i = 0; i < this->alphabetCount; i++){
        char currentLetter = this->alphabet[i];
        letterOccurences[currentLetter] = std::count(subString.begin(), subString.end(), currentLetter);
    }


    double bestSum = 0;
    int bestShift = 0;
    double englishCoincidence = 0.065;

    for (int i = 0; i < this->alphabetCount; i++ ) {

        double sum = 0;
        for (int j = 0; j < this->alphabetCount; j++) {
            char  letterAfterShift = alphabet[(j + i)  % this->alphabetCount];
            float currentLetterProb = probability[j];

            sum += (currentLetterProb * letterOccurences[letterAfterShift]) / subString.size();
        }

        if (std::fabs(bestSum - englishCoincidence) > std::fabs(sum - englishCoincidence)) {
            bestSum = sum;
            bestShift = i;
        }

    }

    return alphabet[bestShift];
}
