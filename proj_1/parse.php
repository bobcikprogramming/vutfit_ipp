<?php

/** 
 * Název:       parse.php
 * Předmět:     Principy programovacích jazyků a OOP
 * Instituce:   VUT FIT
 * Autor:       Pavel Bobčík
 * Login:       xbobci03
 * vytvořeno:   18. únor 2021 
 **/


ini_set("display_errors", "stderr");

/** 
 * Konstany reprezentující exit code.
 **/
define("correct", 0);
define("paramErron", 10);
define("headerError", 21);
define("opcodeError", 22);
define("lexOrSynError", 23);


checkArg($argc, $argv);
parse();
exit(correct);



/******************
 * Pomocné funkce *
 ******************/

/**
 * Jedná se o hlavní funkci parseru. Prochází v cyklu, dokud může načíst nový řádek.
 * Jako první provede za pomocí pomocných funkcí počáteční režii, jako je smazání mezer či konce řádku 
 * nebo přeskočení white sekvencí.
 * Dále se zkontroluje, v případě, že stále nebyla nalezena hlavička, zda-li se vyskytuje na daném řádku.
 * Pokud nenalezneme hlavičku, nebo ji nalezneme chybnou, program se ukončí s chybou.
 * Další řádky si rozdělíme na po jednotlivých částích rozdělených mezerou/mezerami.
 * Tyto části budeme pomocí switch kontrolovat a to jako keywords. Najdeme-li neplatný, ukončujeme s chybou.
 * Jednotlivá keywords rozdělíme dle jejich neterminálů, a podle jejich zařazení nad nimi voláme pomocné funkce,
 * na kontrolu daných neterminálů.
 **/
function parse()
{
    $hasHeader = false;
    $orderNum = 1;

    echo ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");

    while ($line = fgets(STDIN)) {
        /** 
         *  Pokud se na řádku vyskytuje komentář, tak se zavolá funkce removeComment,
         *  která jej, společně s #, smaže. 
         **/
        if (preg_match("/#/", $line)) {
            $line = removeComments($line);
        }
        /**
         * Odstranění konce řádku.
         * Odstranění bílých znaků před operačním kódem a na konci řádku.
         **/
        $line = removeBegAndEndSpacesAndEndfOfLine($line);

        // Přeskočení white space sekvencí.
        if ($line == "" || ctype_space($line)) {
            continue;
        }

        // Kontrola, zda-li se vyskytuje hlavička.
        if ($hasHeader == false) {
            if (checkHeader($line)) {
                $hasHeader = true;
            } else {
                errorCode("Chybná nebo chybějící hlavička ve zdrojovém kódu zapsaném v IPPcode21.", headerError);
            }
        } else {

            $split = preg_split("/\s+/", $line);
            switch (strtoupper($split[0])) {
                    // NIC
                case "RETURN":
                case "BREAK":
                case "CREATEFRAME":
                case "PUSHFRAME":
                case "POPFRAME":
                    if (sizeof($split) != 1) {
                        errorCode("Chybný počet neterminálů.", lexOrSynError);
                    }
                    echo ("\t<instruction order=\"" . $orderNum . "\" opcode=\"" . strtoupper($split[0]) . "\">\n");
                    echo ("\t</instruction>\n");
                    $orderNum++;
                    break;

                    // VAR
                case "POPS":
                case "DEFVAR":
                    if (sizeof($split) != 2) {
                        errorCode("Chybný počet neterminálů.", lexOrSynError);
                    }
                    echo ("\t<instruction order=\"" . $orderNum . "\" opcode=\"" . strtoupper($split[0]) . "\">\n");
                    hasVar($split, 1);
                    echo ("\t</instruction>\n");
                    $orderNum++;
                    break;

                    // LABEL
                case "CALL":
                case "LABEL":
                case "JUMP":
                    if (sizeof($split) != 2) {
                        errorCode("Chybný počet neterminálů.", lexOrSynError);
                    }
                    echo ("\t<instruction order=\"" . $orderNum . "\" opcode=\"" . strtoupper($split[0]) . "\">\n");
                    hasLabel($split, 1);
                    echo ("\t</instruction>\n");
                    $orderNum++;
                    break;

                    // SYMB
                case "PUSHS":
                case "WRITE":
                case "EXIT":
                case "DPRINT":
                    if (sizeof($split) != 2) {
                        errorCode("Chybný počet neterminálů.", lexOrSynError);
                    }
                    echo ("\t<instruction order=\"" . $orderNum . "\" opcode=\"" . strtoupper($split[0]) . "\">\n");
                    hasSymb($split, 1);
                    echo ("\t</instruction>\n");
                    $orderNum++;
                    break;

                    // VAR SYMB
                case "MOVE":
                case "INT2CHAR":
                case "TYPE":
                case "NOT":
                case "STRLEN":
                    if (sizeof($split) != 3) {
                        errorCode("Chybný počet neterminálů.", lexOrSynError);
                    }
                    echo ("\t<instruction order=\"" . $orderNum . "\" opcode=\"" . strtoupper($split[0]) . "\">\n");
                    hasVar($split, 1);
                    hasSymb($split, 2);
                    echo ("\t</instruction>\n");
                    $orderNum++;
                    break;

                    // VAR TYPE
                case "READ":
                    if (sizeof($split) != 3) {
                        errorCode("Chybný počet neterminálů.", lexOrSynError);
                    }
                    echo ("\t<instruction order=\"" . $orderNum . "\" opcode=\"" . strtoupper($split[0]) . "\">\n");
                    hasVar($split, 1);
                    hasType($split, 2);
                    echo ("\t</instruction>\n");
                    $orderNum++;
                    break;

                    // VAR SYMB SYMB
                case "ADD":
                case "SUB":
                case "MUL":
                case "IDIV":
                case "LT":
                case "GT":
                case "EQ":
                case "AND":
                case "OR":
                case "STRI2INT":
                case "CONCAT":
                case "GETCHAR":
                case "SETCHAR":
                    if (sizeof($split) != 4) {
                        errorCode("Chybný počet neterminálů.", lexOrSynError);
                    }
                    echo ("\t<instruction order=\"" . $orderNum . "\" opcode=\"" . strtoupper($split[0]) . "\">\n");
                    hasVar($split, 1);
                    hasSymb($split, 2);
                    hasSymb($split, 3);
                    echo ("\t</instruction>\n");
                    $orderNum++;
                    break;

                    // LABEL SYMB SYMB
                case "JUMPIFEQ":
                case "JUMPIFNEQ":
                    if (sizeof($split) != 4) {
                        errorCode("Chybný počet neterminálů.", lexOrSynError);
                    }
                    echo ("\t<instruction order=\"" . $orderNum . "\" opcode=\"" . strtoupper($split[0]) . "\">\n");
                    hasLabel($split, 1);
                    hasSymb($split, 2);
                    hasSymb($split, 3);
                    echo ("\t</instruction>\n");
                    $orderNum++;
                    break;
                default:
                    errorCode("Neznámý nebo chybný operační kód ve zdrojovém kódu zapsaném v IPPcode21.", opcodeError);
            }
        }
    }
    if ($hasHeader == false) {
        errorCode("Chybná nebo chybějící hlavička ve zdrojovém kódu zapsaném v IPPcode21.", headerError);
    }
    echo ("</program>");
}

/**
 * Kontroluje správnost neterminálu var. Pomocí regexu kontroluje správný název. 
 * V případě výskytu specifického znaku provede jeho nahrazení.
 * Neprojde-li kontrolou, dojde k ukončení s chybou.
 * @param split textový řetězec obsahující zkoumaný neterminál
 * @param numOfNonTerm pořadí neterminálu
 **/
function hasVar($split, $numOfNonTerm)
{
    if (preg_match("/^(LF|GF|TF)@[a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*$/", $split[$numOfNonTerm])) {
        $split[$numOfNonTerm] = str_replace("&", "&amp;", $split[$numOfNonTerm]);
        echo ("\t\t<arg" . $numOfNonTerm . " type=\"var\">" . $split[$numOfNonTerm] . "</arg" . $numOfNonTerm . ">\n");
    } else {
        errorCode("Chybný formát neterminálu VAR.", lexOrSynError);
    }
}

/**
 * Kontroluje správnost neterminálu label. Pomocí regexu kontroluje správný název. 
 * V případě výskytu specifického znaku provede jeho nahrazení.
 * Neprojde-li kontrolou, dojde k ukončení s chybou.
 * @param split textový řetězec obsahující zkoumaný neterminál
 * @param numOfNonTerm pořadí neterminálu
 **/
function hasLabel($split, $numOfNonTerm)
{
    if (preg_match("/^[a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*$/", $split[$numOfNonTerm])) {
        $split[$numOfNonTerm] = str_replace("&", "&amp;", $split[$numOfNonTerm]);
        echo ("\t\t<arg" . $numOfNonTerm . " type=\"label\">" . $split[$numOfNonTerm] . "</arg" . $numOfNonTerm . ">\n");
    } else {
        errorCode("Chybný formát neterminálu LABEL.", lexOrSynError);
    }
}

/**
 * Kontroluje správnost neterminálu type, a tedy že se jedná o jeden z povolených typů (int/string/bool).
 * Neprojde-li kontrolou, dojde k ukončení s chybou.
 * @param split textový řetězec obsahující zkoumaný neterminál
 * @param numOfNonTerm pořadí neterminálu
 **/
function hasType($split, $numOfNonTerm)
{
    if (
        strcmp($split[$numOfNonTerm], "int") == 0
        || strcmp($split[$numOfNonTerm], "string") == 0
        || strcmp($split[$numOfNonTerm], "bool") == 0
    ) {
        echo ("\t\t<arg" . $numOfNonTerm . " type=\"type\">" . $split[$numOfNonTerm] . "</arg" . $numOfNonTerm . ">\n");
    } else {
        errorCode("Chybný formát neterminálu TYPE.", lexOrSynError);
    }
}

/**
 * Kontroluje správnost neterminálu symb. Pomocí regexu kontroluje správný název. 
 * Dále pro jednotlivé typy konstant kontroluje jejich specifikace.
 * Pro string zpracovává speciální znaky a kontroluje výskyt dekadických čísel.
 * Pro bool kontroluje, zdali obsahuje pouze hodnoty true nebo false.
 * U nil se kontroluje, že obsahuje pouze nil.
 * A u integeru, že se jedná o celé číslo.
 * V případě, že nějaká z kontrol neprojde, dojde k ukončení s chybou.
 * @param split textový řetězec obsahující zkoumaný neterminál
 * @param numOfNonTerm pořadí neterminálu
 **/
function hasSymb($split, $numOfNonTerm)
{
    if (preg_match("/^(LF|GF|TF)@[a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*$/", $split[$numOfNonTerm])) {
        $split[$numOfNonTerm] = str_replace("&", "&amp;", $split[$numOfNonTerm]);
        echo ("\t\t<arg" . $numOfNonTerm . " type=\"var\">" . $split[$numOfNonTerm] . "</arg" . $numOfNonTerm . ">\n");
    } else if (preg_match("/^string@[^\s#]*$/", $split[$numOfNonTerm])) {
        $splitSymb = explode('@', $split[$numOfNonTerm]);
        $restOfSplit = str_replace($splitSymb[0] . "@", "", $split[$numOfNonTerm]);

        if ($splitSymb[0] == "string") {
            $restOfSplit = str_replace("&", "&amp;", $restOfSplit);
            $restOfSplit = str_replace("<", "&lt;", $restOfSplit);
            $restOfSplit = str_replace(">", "&gt;", $restOfSplit);
            $restOfSplit = str_replace("'", "&apos;", $restOfSplit);

            // Kontroluje výskyt '\' v řetězci
            if (
                preg_match_all("/\\\\/", $split[$numOfNonTerm])
                && (preg_match("/(\\\\([^0-9]|[0-9][^0-9]|[0-9][0-9][^0-9])|\\\\$)/", $split[$numOfNonTerm]))
            ) {
                errorCode("Nepovolený výskyt znaku '\' v řetězci.", lexOrSynError);
            }
        }

        echo ("\t\t<arg" . $numOfNonTerm . " type=\"" . $splitSymb[0] . "\">" . $restOfSplit . "</arg" . $numOfNonTerm . ">\n");
    } else if (
        preg_match("/^bool@(true|false)$/", $split[$numOfNonTerm])
        || preg_match("/^nil@nil$/", $split[$numOfNonTerm])
        || preg_match("/^int@[+-]?[0-9]+$/", $split[$numOfNonTerm])
    ) {
        $splitSymb = explode('@', $split[$numOfNonTerm]);
        $restOfSplit = str_replace($splitSymb[0] . "@", "", $split[$numOfNonTerm]);
        echo ("\t\t<arg" . $numOfNonTerm . " type=\"" . $splitSymb[0] . "\">" . $restOfSplit . "</arg" . $numOfNonTerm . ">\n");
    } else {
        errorCode("Chybný formát neterminálu SYMB.", lexOrSynError);
    }
}

/**
 * Odstraní text následující za symbolem značácí komentář.
 * @param line textový řetězec obsahující upravovaný řádek
 * @return newLine vrací textový řetězec bez textu vyskytujícím se za znakem komentáře
 **/
function removeComments($line)
{
    $newLine = "";
    $charNum = 0;

    while ($line[$charNum] != "#") {
        $newLine .= $line[$charNum];
        $charNum++;
    }

    return $newLine;
}

/**
 * Funkce sloužící pro kontrolu parametrů na vstupu.
 * V případě výskytu parametru "--help" vypíše nápovědu.
 * Při výskytu jiného parametru dojde k ukončení za využití pomocné funkce errorCode.
 * @param argc počet parametrů
 * @param argv textové pole parametrů
 **/
function checkArg($argc, $argv)
{
    if ($argc > 1) {
        if ($argc > 2) {
            errorCode("Chybný počet parametrů.", paramErron);
        } else {
            if ($argv[1] != "--help") {
                errorCode("Chybný parametr.", paramErron);
            } else {
                echo ("Použití: php[verze] parse.php <vstupníSoubor\n");
                exit(0);
            }
        }
    }
}

/**
 * Pomocná funkce na výpis chybového hlášení a exit code.
 * @param errorMess textový řetězec obsahující chybové hlášení
 * @param errorNum integer obsahující hodnotu exit code
 **/
function errorCode($errorMess, $errorNum)
{
    fwrite(STDERR, $errorMess . "\n");
    exit($errorNum);
}

/**
 * Funkce k odstranění mezer na začátku a konci řádku, dále k odstranění znaku konce řádku.
 * @param line textový řetezěc obsahující řádek ke zpracování
 * @return error textový řetězec obsahující zpracovaný řádek
 **/
function removeBegAndEndSpacesAndEndfOfLine($line)
{
    $line = str_replace("\n", "", $line);
    $line = preg_replace("/^\s+/", "", $line);
    $line = preg_replace("/\s+$/", "", $line);
    return $line;
}

/**
 * Pomocná funkce na kontrolu hlavičky.
 * @param line textový řetezěc obsahující řádek ke kontrole
 * @return bool vrací zda-li našel, či nikoliv.
 **/
function checkHeader($line)
{
    $line = strtoupper($line);
    if (preg_match("/(^.IPPCODE21$)/", $line)) {
        echo ("<program language=\"IPPcode21\">\n");
        return true;
    } else {
        return false;
    }
}
