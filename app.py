import streamlit as st
from callbacks import (
    init_app, reset_app, set_ss, copy_ss, search_callback,
    process_file, search_pdf, generate_answer)


colors = ['red', 'blue', 'green', 'violet', 'orange']
output_text = '**Authors**: {authors}\n\n**Subjects**: {subjects}'
widget_keys = [('_check_{id}', False), ('_file_{id}', None), ('_searched_{id}', False)]
init_data = [('_query_results', []), ('_selected_ids', {}), ('_answer', '')]

init_app(init_data)

st.title('LLMs and RAG')
topic = st.text_input(label='**What do you want to know?**')
search_btn = st.button(
    label='Search docs',
    disabled=(not topic),
    on_click=search_callback,
    args=(topic,)
)

if (query_results := st.session_state.get('_query_results', {})):
    st.subheader('Related Books')
    st.markdown('**Select the books that do you want me to use to explain your topic**')
    st.caption(':lock: **not processed**    :unlock: **available**    :white_check_mark: **selected**')
    hide = st.checkbox(label='Hide documents')
    if not hide:
        for id, book in query_results.items():
            title, active, processed, link, subjects, authors = (
                    book.get('title'), book.get('active'),
                    book.get('processed'), book.get('link'),
                    book.get('subjects'), book.get('authors')
            )
            subjects = ' '.join(f':{colors[i % 5]}-background[{s}]' for i, s in enumerate(subjects.split('; ')))
            for key, val in widget_keys:
                key_ = key.format(id=id)
                if key_ not in st.session_state:
                    set_ss(key_, val)
            check_value = st.session_state.get(f'check_{id}', False)
            if processed:
                if check_value:
                    emoji = ':white_check_mark:'
                else:
                    emoji = ':unlock:'
            elif not active:
                emoji = ':clown_face:'
            else:
                emoji = ':lock:'

            with st.expander(label=f'**{title}** {emoji}'):
                st.write(output_text.format(authors=authors, subjects=subjects))
                copy_ss(f'_check_{id}', f'check_{id}')
                check = st.checkbox(
                    label='Use for RAG.',
                    key=f'check_{id}', on_change=copy_ss,
                    args=(f'check_{id}', f'_check_{id}'),
                    disabled=(not active)
                )
                if check:
                    if not processed:
                        if not st.session_state[f'_searched_{id}']:
                            st.button(
                                label='Search pdf', 
                                key=f'sbtn_{id}',
                                on_click=search_pdf,
                                args=(id, link)
                            )
                        else:
                            file = st.file_uploader(
                                label=f'Upload the book (available [here :link:]({link}))',
                                    key=f'file_{id}', on_change=copy_ss,
                                    args=(f'file_{id}', f'_file_{id}')
                                )
                            st.button(
                                    label='Process', 
                                    disabled=(not file),
                                    key=f'pbtn_{id}',
                                    on_click=process_file,
                                    args=(id, file)
                            )
                    else:
                        st.session_state['_selected_ids'][id] = True
                else:
                    st.session_state['_selected_ids'][id] = False

    selected_ids = [k for k, v in st.session_state['_selected_ids'].items() if v]
    col1, col2, _ = st.columns([0.15, 0.15, 0.7])
    col1.button(
        label='Generate',
        disabled=(not selected_ids),
        key='gen_btn',
        on_click=generate_answer,
        args=(topic, selected_ids)
    )
    col2.button(label='Reset', key='reset_btn', on_click=reset_app)

    if (answer := st.session_state.get('_answer')):
        st.subheader('Response')
    st.markdown(f':brain: {answer}')
