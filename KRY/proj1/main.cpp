#include "KeyFinder.h"
#include "friedman.cpp"
#include "kasiski.cpp"
#include "iostream"
#include "iterator"

int main () {
    std::cin >> std::noskipws;
    std::istream_iterator<char> it(std::cin);
    std::istream_iterator<char> end;
    std::string results(it, end);

    std::string input = results;

    input.erase(std::remove_if(input.begin(), input.end(), [](unsigned char x){return not std::isalpha(x);}), input.end());
    std::transform(input.begin(), input.end(), input.begin(),
                   [](unsigned char c){ return std::tolower(c); });

    double friedmanResult = friedman_test(input);
    std::vector<std::pair<int, int> > kasiskiFactors = kasiskiTest(input);

    auto iter = kasiskiFactors.begin();
    int kasiskiResult = iter->first;


    int myKeyLenght = 0;
    int checkFirstNkeys = 10;
    double maxIC = 0;
    for (int i = 0; i < checkFirstNkeys; i++){
        std::pair<int, int> currentFactor = kasiskiFactors[i];
        int keyLength = currentFactor.first;
        if (kasiskiResult == 2) {
            kasiskiResult = keyLength;
        }

        if (keyLength > 2.1 * friedmanResult and kasiskiResult < 2 * friedmanResult){
            continue;
        }

        KeyFinder newKey (keyLength, input);
        double newIC = newKey.countAverageCoincidence();

        if (maxIC < newIC) {
            maxIC = newIC;
            myKeyLenght = keyLength;
        }
    }


    KeyFinder key (myKeyLenght, input);
    std::string foundKey = key.findKey();

    printf("%.2f;%d;%d;%s\n", friedmanResult, kasiskiResult, myKeyLenght, foundKey.c_str());

}



