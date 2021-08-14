//
// Created by Andrej Zaujec on 03/04/2021.
//
#include "set"
#include "Ngram.h"

bool customVectorComparison(const std::pair<int, int> &a, const std::pair<int, int> &b);

std::set<int> computeDividers(int number) {
    std::set<int> dividers;
    int currentDivider = 2;
    while (currentDivider < number) {
        if (number % currentDivider == 0) {
            dividers.insert(currentDivider);
        }
        currentDivider++;
    }

    dividers.insert(number);
    return dividers;
}

std::set<int> getDividers(int number, std::map<int, std::set<int>> common_dividers) {
    std::map<int, std::set<int>>::iterator foundElement = common_dividers.find(number);
    if (foundElement == common_dividers.end()) {
        std::set<int> newDividers = computeDividers(number);
        common_dividers.insert({number, newDividers});
        return newDividers;
    }
    return foundElement->second;
}


std::vector<std::pair<int, int>> kasiskiTest(std::string input) {

    int lowestNgram = 4;
    int highestNgram = 7;

    std::map<int, std::set<int>>commonDividers;
    std::map<int, int> factorCounter;

    for (int i = lowestNgram; i <= highestNgram; i++) {
        Ngram ngrams(input.c_str(), strlen(input.c_str()), i);
        NgramOccurenceNode ngramFrequency = ngrams.find_ngrams();

        std::vector<int> distanceOccurrence;
        NgramOccurenceNode *currentNode = &ngramFrequency;
        while (currentNode) {
            if (currentNode->freq > 1) {
                distanceOccurrence.insert(std::end(distanceOccurrence), std::begin(currentNode->distances),
                                          std::end(currentNode->distances));
            }
            currentNode = currentNode->next;


        }

        std::set<int, std::greater<int>> uniqueDistances(distanceOccurrence.begin(), distanceOccurrence.end());
        auto it = uniqueDistances.begin();

        while (it != uniqueDistances.end()) {
            int distance = *it;
            std::set<int> distanceDividers = getDividers(distance, commonDividers);

            auto div_it = distanceDividers.begin();
            while (div_it != distanceDividers.end()) {
                factorCounter[*div_it]++;
                ++div_it;
            }
            ++it;

        }
    }


    std::vector<std::pair<int, int>> sortedOccurances;
    auto it = factorCounter.begin();
    while (it != factorCounter.end()) {
        std::pair<int, int> newPair(it->first, it->second);
        sortedOccurances.push_back(newPair);
        ++it;
    }

    sort(sortedOccurances.begin(), sortedOccurances.end(), customVectorComparison);

    return sortedOccurances;
}

bool customVectorComparison(const std::pair<int, int> &a, const std::pair<int, int> &b) {
    return a.second > b.second;
}
