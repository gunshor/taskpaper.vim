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

map <buffer> <silent> <Leader>td :ToggleDone<cr>
map <buffer> <silent> <Leader>tf :Filter 
map <buffer> <silent> <C-a> :AddToDate<cr>
map <buffer> <silent> <C-x> :SubFromDate<cr>

augroup TaskpaperBufWritePre
  au!
  au BufWritePre *.taskpaper silent py run_presave()
  au BufWritePost *.taskpaper silent checktime
augroup END

if exists("loaded_task_paper")
    finish
endif
let loaded_task_paper = 1

command -nargs=* Filter py filter_taskpaper(r'<args>')
command -count AddToDate py add_to_date(<count>, 1)
command -count SubFromDate py add_to_date(<count>, -1)
command -range ToggleDone py toggle_done(<count>)

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
from taskpaper.vim_utils import *
EOF
" }}}

