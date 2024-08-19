import streamlit as st
from callbacks import (
    init_app, reset_app, set_ss, copy_ss, search_callback,
    process_upload_file, extract_excerpts, search_pdf)

output_text = '**Authors**: {authors}\n\n**Subjects**: {subjects}'
widget_keys = [('_check_{id}', False), ('_upload_{id}', None),]
init_data = [('_query_results', []), ('_selected_ids', {}), ('_excerpts', [])]

init_app(init_data)

st.title('LLMs and RAG')
topic = st.text_input(label='**What do you want to know?**')
search_btn = st.button(
    label='Search',
    disabled=(not topic),
    on_click=search_callback,
    args=(topic,)
)

if (query_results := st.session_state.get('_query_results', {})):
# ans, finish = generate_text(topic)
    st.subheader('')
    for id, book in query_results.items():
        title, active, processed, link = book.get('title'), book.get('active'), book.get('processed'), book.get('link')
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
            st.write(output_text.format(**book))
            copy_ss(f'_check_{id}', f'check_{id}')
            check = st.checkbox(
                label='Use for RAG.',
                key=f'check_{id}', on_change=copy_ss,
                args=(f'check_{id}', f'_check_{id}'),
                disabled=(not active)
            )
            if check:
                if not processed:

                    st.button(
                        label='Process', 
                        key=f'sbtn_{id}',
                        on_click=search_pdf,
                        args=(link, )
                    )
                    if not file:
                        file = st.file_uploader(
                            label='Upload the book (available at the link)',
                            key=f'upload_{id}', on_change=copy_ss,
                            args=(f'upload_{id}', f'_upload_{id}')
                        )
                    st.button(
                        label='Process', 
                        disabled=(not file),
                        key=f'pbtn_{id}',
                        on_click=process_upload_file,
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
        on_click=extract_excerpts,
        args=(topic, selected_ids)
    )
    col2.button(label='Reset', key='reset_btn', on_click=reset_app)

    if (excerpts := st.session_state.get('_excerpts', [])):
        header2 = 'Excerpts'
        for i, e in enumerate(excerpts):
            st.write(f'#### Excerpt {i + 1}\n\n{e}')

st.write(st.session_state)
