#!/bin/bash
function prepare () {
    # https://askubuntu.com/questions/271776/how-to-resize-an-image-through-the-terminal
    # https://qiita.com/sowd/items/832594dd22d99aebc8a2
    # サイズを変換
    rm -rf "${1}-${2}"
    mkdir "${1}-${2}"
    for n in $1/*.png; do
        newfname=$(echo "${n}" | sed "s/${1}/${1}-${2}/g")
        convert -resize "${2}x${2}" "${n}" "${newfname}"
    done
    # スプライト作成
    rm "sprite/${1}-${2}.css"
    glue "${1}-${2}" sprite --css-template sprite/css-template.css --sprite-namespace "${3}" --margin 1
    # if [ -n $3 ]; then
    #   glue "${1}-${2}" sprite --css-template sprite/css-template.css --sprite-namespace "${3}"
    # else
    #   glue "${1}-${2}" sprite --css-template sprite/css-template.css 
    # fi
    #glue "${1}-${2}" sprite
}
prepare hero 116 hero-116-80
prepare hero 80 hero-116-80
prepare hero 64 hero-64
prepare hero 32 hero-32
prepare items 48 items-48-38
prepare items 38 items-48-38
#prepare tiers 640

function scale () {
  cat sprite/$1-$2.css sprite/_media-460-begin.css sprite/$1-$3.css sprite/_media-460-end.css > sprite/$1-$2-$3.css
}
#cat sprite/hero-116.css sprite/_media-460-begin.css sprite/hero-80.css sprite/_media-460-end.css > sprite/hero-116-80.css
scale hero 116 80
scale items 48 38

# function e () {
#     echo "${1}-${2}"
# }
# e items 64
