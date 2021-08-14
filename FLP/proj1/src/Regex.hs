{-|
Login: xzauje00
Author: Andrej Zaujec
Project: rv-2-rka(FLP)
Year: 2021
|-}
module Regex where

import FiniteMachine (concatenateFSMs, unionFSMs, iterateFSM, createFromCharFSM, FSMachine)
import Helpers (Err)

import Control.Applicative ((<$>), (<*>), (<$), (*>), (<*), (<|>))
import Control.Arrow (left)
import Control.Monad ((<=<), void)
import Data.Set (Set, fromList, toList, singleton)
import Data.Char (isSpace)
import Text.Parsec (Parsec, parse,
        oneOf, newline, manyTill, alphaNum, string, char, satisfy, sepBy1, endBy, many1, choice, between, eof, try)
import Text.Parsec.String (Parser)

data Regex = Character Char
          | Atom Regex
          | AtomWithStar Regex
          | Factor Regex
          | TermRest Regex Regex
          | Term Regex Regex
          | RegexpRest Regex Regex
          | Regexp Regex Regex
          | EndOfRule
          | Epsilon

instance Show Regex where
  show = showRegex

showRegex (Regexp a (RegexpRest x y)) = show a ++ "+" ++ show (RegexpRest x y)
showRegex (Regexp a b) = show a ++ show b
showRegex (AtomWithStar a) = show a ++ "*"
showRegex (Character a) =  [a]
showRegex EndOfRule = ""
showRegex (Atom (Regexp a b)) = "(" ++ show a ++ show b ++ ")"
showRegex (Atom a) = showRegex a
showRegex (Factor a) = showRegex a
showRegex (TermRest a b) = showRegex a ++ showRegex b
showRegex (Term a b) = showRegex a ++ showRegex b
showRegex (RegexpRest a b) = showRegex a ++ showRegex b
showRegex Epsilon = "#"

characterP :: Parser Regex
characterP = (Character <$> oneOf ['a'..'z']) <|> (Epsilon <$ char '#')

epsilonP :: Parser Regex
epsilonP = EndOfRule <$ string ""

atomP :: Parser Regex
atomP = Atom <$> ((char '(' *> regexP <* char ')') <|> characterP )

atomWithStar :: Parser Regex
atomWithStar = AtomWithStar <$> atomP <* char '*'

factorP :: Parser Regex
factorP = Factor <$> try atomWithStar <|> atomP

termRestLeftP :: Parser Regex
termRestLeftP = TermRest <$> factorP <*> termRestP

termRestP :: Parser Regex
termRestP = termRestLeftP <|> epsilonP

termP :: Parser Regex
termP = Term <$> factorP <*> termRestP

regexRestP :: Parser Regex
regexRestP = (RegexpRest <$> (char '+' *> termP) <*> regexRestP) <|> epsilonP

regexP :: Parser Regex
regexP = Regexp <$> termP <*> regexRestP

mainP :: Parser Regex
mainP = regexP <* eof


parseRegex :: String -> Err Regex
parseRegex input = parsedRegex where
  preparedString = filter (not . isSpace) input
  parsedRegex = case parse mainP "" preparedString of
    Left a -> Left "Error: invalid regex"
    Right a -> Right a

regexToFSM :: Int -> Regex -> (FSMachine, Int)
regexToFSM stateCount regex = case regex of
  (Regexp a EndOfRule) -> regexToFSM stateCount a
  (Term a EndOfRule) -> regexToFSM stateCount a
  (TermRest a EndOfRule) -> regexToFSM stateCount a
  (RegexpRest a EndOfRule) -> regexToFSM stateCount a
  (Character a) -> (newFSM, newStateCount) where
    newFSM = createFromCharFSM a stateCount
    newStateCount = stateCount + 2
  (Regexp a b) -> (newFSM, newStateCount) where
    newFSM = unionFSMs (snd secondResult) firstFSM secondFSM
    newStateCount = snd secondResult + 2
    firstResult = regexToFSM stateCount a
    secondResult = regexToFSM (snd firstResult) b
    firstFSM = fst firstResult
    secondFSM = fst secondResult
  (RegexpRest a b) -> regexToFSM' stateCount a b
  (Term a b) -> regexToFSM' stateCount a b
  (TermRest a b) -> regexToFSM' stateCount a b
  (Factor (AtomWithStar a)) -> (newFSM, newStateCount) where
    newFSM = iterateFSM (snd depthResult) depthFSM
    depthResult = regexToFSM stateCount a
    depthFSM = fst depthResult
    newStateCount = snd depthResult + 2
  (Factor a) -> regexToFSM stateCount a
  (Atom a) -> regexToFSM stateCount a
  (AtomWithStar a) -> regexToFSM stateCount a
  Epsilon -> (newFSM, newStateCount) where
    newFSM = createFromCharFSM ' ' stateCount
    newStateCount = stateCount + 2

regexToFSM' :: Int -> Regex -> Regex -> (FSMachine, Int)
regexToFSM' stateCount regex1 regex2 = (newFSM, newStateCount) where
    newFSM = concatenateFSMs firstFSM secondFSM
    newStateCount = snd secondResult
    firstResult = regexToFSM stateCount regex1
    secondResult = regexToFSM (snd firstResult) regex2
    firstFSM = fst firstResult
    secondFSM = fst secondResult
