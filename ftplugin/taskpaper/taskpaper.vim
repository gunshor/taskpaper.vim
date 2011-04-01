" plugin to handle the TaskPaper to-do list format
" Language:	Taskpaper (http://hogbaysoftware.com/projects/taskpaper)
" Maintainer:	David O'Callaghan <david.ocallaghan@cs.tcd.ie>
" URL:		https://github.com/davidoc/taskpaper.vim
" Last Change:  2011-02-15


"add '@' to keyword character set so that we can complete contexts as keywords
setlocal iskeyword+=@-@

"set default folding: by project (syntax), open (up to 99 levels), disabled 
setlocal foldmethod=syntax
setlocal foldlevel=99
setlocal nofoldenable

" Disable wrapping
setlocal nowrap

" Add formatoptions
setlocal formatoptions+=o
setlocal formatoptions+=t
setlocal comments=b:-,b:•

" Filtering
setlocal errorformat=%l:%m

map <buffer> <silent> <Leader>td <Plug>ToggleDone
map <buffer> <silent> <Leader>tx <Plug>ToggleCancelled
map <buffer> <silent> <Leader>tf :Filter 

augroup TaskpaperBufWritePre
  au!
  au BufWritePre *.taskpaper silent py run_presave()
  au BufWritePost *.taskpaper silent checktime
augroup END

if exists("loaded_task_paper")
    finish
endif
let loaded_task_paper = 1

" Define a default date format
if !exists('task_paper_date_format') | let task_paper_date_format = "%Y-%m-%d" | endif
if !exists('task_paper_remap_cr') | let task_paper_remap_cr = 1 | endif

" toggle @done context tag on a task
function! s:ToggleDone()

    let line = getline(".")
    if (line =~ '^\s*- ')
        let repl = line
        if (line =~ '@done')
            let repl = substitute(line, "@done\(.*\)", "", "g")
            echo "undone!"
        else
            let today = strftime(g:task_paper_date_format, localtime())
            let done_str = " @done(" . today . ")"
            let repl = substitute(line, "$", done_str, "g")
            echo "done!"
        endif
        call setline(".", repl)
    else 
        echo "not a task."
    endif

endfunction

" toggle @cancelled context tag on a task
function! s:ToggleCancelled()

    let line = getline(".")
    if (line =~ '^\s*- ')
        let repl = line
        if (line =~ '@cancelled')
            let repl = substitute(line, "@cancelled\(.*\)", "", "g")
            echo "uncancelled!"
        else
            let today = strftime(g:task_paper_date_format, localtime())
            let cancelled_str = " @cancelled(" . today . ")"
            let repl = substitute(line, "$", cancelled_str, "g")
            echo "cancelled!"
        endif
        call setline(".", repl)
    else 
        echo "not a task."
    endif

endfunction

command -nargs=* Filter py filter_taskpaper(r'<args>')

" Set up mappings
noremap <unique> <script> <Plug>ToggleDone       :call <SID>ToggleDone()<CR>
noremap <unique> <script> <Plug>ToggleCancelled   :call <SID>ToggleCancelled()<CR>


"" Python Stuff below {{{

" Expand our path
python << EOF
import vim, os, sys

new_path = vim.eval('expand("<sfile>:h")')
sys.path.append(new_path)

from taskpaper import *
EOF
" }}}

