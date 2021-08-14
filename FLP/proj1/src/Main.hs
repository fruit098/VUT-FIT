{-|
Login: xzauje00
Author: Andrej Zaujec
Project: rv-2-rka(FLP)
Year: 2021
|-}
module Main (main)  where

import System.Environment (getArgs)
import System.Exit (exitFailure)
import System.IO (hPutStrLn, stderr, readFile, getLine, putStr)

import Regex (Regex, parseRegex, regexToFSM)

die :: String -> IO a
die s = hPutStrLn stderr s >> exitFailure

main :: IO ()
main = do
    (action, input) <- procArgs =<< getArgs
    either die action (parseRegex input)

procArgs :: [String] -> IO (Regex -> IO (), String)
procArgs [x,y] = do
    input <- readFile y
    procArgs' x input

procArgs [x] = do
    input <- getLine
    procArgs' x input

procArgs _ = die "expecting two arguments: [-i|-s] FILE"

procArgs' :: String -> String -> IO (Regex -> IO (), String)
procArgs' x input = do
    case x of
     "-i" -> return (dumpRegex, input)
     "-t" -> return (dumpFSM, input)
     _    -> die ("unknown option " ++ x)

dumpRegex :: Regex -> IO ()
dumpRegex reg = do
    print reg

dumpFSM :: Regex -> IO ()
dumpFSM reg = do
  let (fsm, _) = regexToFSM 1 reg
  putStr $ show fsm
