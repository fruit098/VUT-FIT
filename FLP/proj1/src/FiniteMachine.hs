{-|
Login: xzauje00
Author: Andrej Zaujec
Project: rv-2-rka(FLP)
Year: 2021
|-}
{-# LANGUAGE OverloadedStrings, RecordWildCards #-}
module FiniteMachine where

import Data.Set (Set, toList, union, unions, insert, fromList, singleton)
import Data.Char (isSpace)

import Helpers (joinString)

type FSMState = String
type FSMSymbol = Char

data Transition = Trans
    { fromState :: FSMState
    , input :: FSMSymbol
    , toState :: FSMState
    } deriving (Eq, Ord)

instance Show Transition where
  show (Trans fromState ' ' toState) = joinString "," [fromState,"",toState]
  show Trans{..} = joinString "," [fromState,[input],toState]

data FSMachine = FSM
  {states ::Set FSMState,
   alphabet :: Set FSMSymbol,
   transitions :: Set Transition,
   start ::FSMState,
   endState :: FSMState
  } deriving (Eq)

instance Show FSMachine where
  show FSM{..} = unlines $
    [joinString "," $ toList states, alphabetWithoutSpace, start, endState] ++ map show (toList transitions)
    where alphabetWithoutSpace = filter (not . isSpace) (toList alphabet)

concatenateFSMs :: FSMachine -> FSMachine -> FSMachine
concatenateFSMs (FSM states1 alpha1 trans1 start1 end1) (FSM states2 alpha2 trans2 start2 end2) = FSM
  {states = states1 `union` states2
  ,alphabet = alpha1 `union` alpha2
  ,transitions = unions [singleton (Trans end1 ' ' start2), trans1 ,trans2]
  ,start = start1
  ,endState = end2
  }

unionFSMs :: Int -> FSMachine -> FSMachine -> FSMachine
unionFSMs stateNumber (FSM states1 alpha1 trans1 start1 end1) (FSM states2 alpha2 trans2 start2 end2) = FSM
  {states = unions [newStates, states1, states2]
  ,alphabet = alpha1 `union` alpha2
  ,transitions = unions [trans1, trans2, newTransitions]
  ,start = newStart
  ,endState = newEnd
  }

  where newStart = show stateNumber
        newEnd = show $ succ stateNumber
        newStates = fromList [newStart, newEnd]
        newTransitions = fromList
          [Trans newStart ' ' start1
          ,Trans newStart ' ' start2
          ,Trans end1 ' ' newEnd
          ,Trans end2 ' ' newEnd]

iterateFSM :: Int -> FSMachine -> FSMachine
iterateFSM stateNumber (FSM states alpha trans start end) = FSM
  {states = newStates `union` states
  ,alphabet = alpha
  ,transitions = newTransitions `union` trans
  ,start = newStart
  ,endState = newEnd
  }
  where newStart = show stateNumber
        newEnd = show $ succ stateNumber
        newStates = fromList [newStart, newEnd]
        newTransitions = fromList
          [Trans newStart ' ' start
          ,Trans newStart ' ' newEnd
          ,Trans end ' ' start
          ,Trans end ' ' newEnd]

createFromCharFSM :: Char -> Int -> FSMachine
createFromCharFSM character stateNumber = FSM
  {states = newStates
  ,alphabet = singleton character
  ,transitions = singleton (Trans newStart character newEnd)
  ,start = newStart
  ,endState = newEnd}

  where newStart = show stateNumber
        newEnd = show $ succ stateNumber
        newStates = fromList [newStart, newEnd]
