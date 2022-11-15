import React from 'react';
import PropTypes from 'prop-types';
import Dropzone from "react-dropzone";
import { humanReadableBytes } from "react-invenio-deposit";
import FileTable from "./FileTable";

const FileUploader = ({ dropzoneParams, maxFileSize, name, currentFiles, handleDelete }) => {
    return (
        <Dropzone {...dropzoneParams}>
            {({ getRootProps, getInputProps }) => {
                const inpProps = {
                    ...getInputProps(),
                    // Display the dropzone input, otherwise it's hidden by default.
                    style: {
                        'display': 'block'
                    },
                    name: name
                }
                return (
                    <div {...getRootProps()}>
                        <input {...inpProps} />
                        <label className="helptext mt-0">
                            {`Optional. Max attachments size: ${humanReadableBytes(maxFileSize, false)}`}
                        </label>
                        {currentFiles.length > 0
                            &&
                            <FileTable
                                handleDelete={handleDelete}
                                filesList={currentFiles}
                            />
                        }
                    </div>
                )
            }}
        </Dropzone>
    );
};

FileUploader.propTypes = {
    dropzoneParams: PropTypes.object.isRequired,
    maxFileSize: PropTypes.number.isRequired,
    name: PropTypes.string.isRequired,
    currentFiles: PropTypes.array.isRequired
};

export default FileUploader;