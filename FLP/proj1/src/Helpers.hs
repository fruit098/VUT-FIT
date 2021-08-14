{-|
Login: xzauje00
Author: Andrej Zaujec
Project: rv-2-rka(FLP)
Year: 2021
|-}
module Helpers where

joinString :: String -> [String] -> String
joinString _ [] = ""
joinString _ [x] = x
joinString joiner (x:xs) = x ++ joiner ++ joinString joiner xs

type Err = Either String
