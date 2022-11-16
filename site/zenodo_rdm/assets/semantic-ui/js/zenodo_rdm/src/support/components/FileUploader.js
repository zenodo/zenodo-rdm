import React from 'react';
import PropTypes from 'prop-types';
import Dropzone from "react-dropzone";
import { humanReadableBytes } from "react-invenio-deposit";
import FileTable from "./FileTable";

const FileUploader = ({ dropzoneParams, maxFileSize, name, currentFiles, handleDelete }) => {
    return (
        <div>
            <Dropzone {...dropzoneParams}>
                {({ getRootProps, getInputProps }) => (
                    <div id="file-dropzone" {...getRootProps({className: "dropzone"})}>
                        <input {...getInputProps()} name={name} />
                        <p className="ui medium header text-align-center m-0">
                            Drag files here, or click to select files
                        </p>
                    </div>
                )}
            </Dropzone>

            <label className="helptext mt-5">
                {`Optional. Max attachments size:`} {humanReadableBytes(maxFileSize, false)}
            </label>

            {currentFiles.length > 0
                &&
                <FileTable
                    handleDelete={handleDelete}
                    filesList={currentFiles}
                />
            }
        </div>
    );
};

FileUploader.propTypes = {
    dropzoneParams: PropTypes.object.isRequired,
    maxFileSize: PropTypes.number.isRequired,
    name: PropTypes.string.isRequired,
    currentFiles: PropTypes.array.isRequired
};

export default FileUploader;