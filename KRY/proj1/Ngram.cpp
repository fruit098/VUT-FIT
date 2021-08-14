//
// Created by Andrej Zaujec on 29/03/2021.
//

#include "Ngram.h"

#include <algorithm>
#include <cstring>
#include "vector"
#include "map"

struct NgramOccurenceNode {
    const char *str;
    unsigned int freq;
    NgramOccurenceNode *prev;
    NgramOccurenceNode *next;
    std::vector <int> distances;
    const char *originalPosition;

};

class Ngram {
    unsigned int inputSize;
    unsigned short ngramsSize;
    unsigned int ngramsCount;
    char *ngrams;
    const char *input;
    std::map <int,const char *> pointerPerNgramIndex;

public:
    Ngram(const char *input_string, int input_size, int ngram_size) {
        this->input = input_string;
        this->inputSize = input_size;
        this->ngramsSize = ngram_size;
        this->ngramsCount = inputSize;
        this->ngrams = new char[ngramsCount * (ngramsSize + 1)];
    }

    ~Ngram(){
        delete this->ngrams;

    }

    bool notTerminated(const char *ptr);
    NgramOccurenceNode find_ngrams();
    size_t index( int x, int y );

    void insertFreqNode(NgramOccurenceNode *orig, char *ptr, int ngramIndex);

};
size_t Ngram::index(int x, int y) { return x * sizeof (char) * (ngramsSize + 1) + y * sizeof (char);};


bool Ngram::notTerminated(const char *ptr) {
    for (int i = 0; i < ngramsSize; i++) {
        if (ptr[i] == '\0') {
            return false;
        }
    }
    return true;
}

void unlink(NgramOccurenceNode *node) {
    NgramOccurenceNode *prev = node->prev;
    NgramOccurenceNode *next = node->next;
    if (prev && prev->next) {
        prev->next = next;
    }
    if (next && next->prev) {
        next->prev = prev;
    }
    node->next = 0;
    node->prev = 0;
}

void insertAfter(NgramOccurenceNode *insert, NgramOccurenceNode *after) {
    NgramOccurenceNode *origNext = after->next;
    after->next = insert;
    insert->prev = after;
    origNext->prev = insert;
    insert->next = origNext;
}


void Ngram::insertFreqNode(NgramOccurenceNode *orig, char *ptr, int ngramIndex) {
    int freq = 0;
    NgramOccurenceNode *current_node = orig;
    NgramOccurenceNode *origHead = current_node;
    bool needInsert = true;
    while (current_node->next) {
        freq = origHead->next->freq;
        if (strcmp(current_node->next->str, ptr) == 0) {
            current_node->next->distances.push_back(this->pointerPerNgramIndex[ngramIndex] - current_node->next->originalPosition);
            current_node->next->freq += 1;
            if (current_node->next->freq >= freq
                && origHead->next != current_node->next) {
                NgramOccurenceNode *link = current_node->next;
                unlink(link);
                insertAfter(link, origHead);
            }
            needInsert = false;
            break;
        }
        current_node = current_node->next;
    }
    if (needInsert) {
        NgramOccurenceNode *newNode = new NgramOccurenceNode();
        newNode->prev = current_node;
        newNode->next = 0;
        newNode->str = ptr;
        newNode->freq = 1;
        newNode->originalPosition = this->pointerPerNgramIndex[ngramIndex];
        current_node->next = newNode;
    }
}

NgramOccurenceNode Ngram::find_ngrams() {
    const char *ptr = this->input;
    int idx = 0;

    while (notTerminated(ptr)) {
        this->pointerPerNgramIndex[idx] = ptr;
        for (int i = 0; i < ngramsSize; i++) {
            ngrams[index(idx, i)] = ptr[i];
        }
        ngrams[index(idx, ngramsSize)] = '\0';
        idx++;
        ptr++;
    }

    NgramOccurenceNode head = {"\0", 0, 0, 0, std::vector<int> (), 0};
    for (int i = 0; i < ngramsCount; i++) {
        insertFreqNode(&head, &(ngrams[index(i,0)]), i);
    }

    return head;
}

void clearNodes(NgramOccurenceNode *head){
    NgramOccurenceNode *currentNode = head;
    NgramOccurenceNode *nextNode = nullptr;
    while(currentNode){
        nextNode = currentNode->next;
        delete [] currentNode;
        currentNode = nextNode;
    }
}
