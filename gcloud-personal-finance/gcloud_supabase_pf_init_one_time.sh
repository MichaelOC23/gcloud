#!/bin/bash

clear

DNAME="personal-finance"

echo -e "Settting up Supabase"

brew install supabase/tap/supabase
supabase login

supabase init

echo -e "Loggin into project: kioveujteqsynueojotj \n password is in DASHLANE"

supabase link --project-ref "kioveujteqsynueojotj"


