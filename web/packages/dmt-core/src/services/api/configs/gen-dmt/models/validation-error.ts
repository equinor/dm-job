/* tslint:disable */
/* eslint-disable */
/**
 * Data Modelling Tool
 * API for Data Modeling Tool (DMT)
 *
 * The version of the OpenAPI document: 0.1.0
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

/**
 *
 * @export
 * @interface ValidationError
 */
export interface ValidationError {
  /**
   *
   * @type {Array<string | number>}
   * @memberof ValidationError
   */
  loc: Array<string | number>
  /**
   *
   * @type {string}
   * @memberof ValidationError
   */
  msg: string
  /**
   *
   * @type {string}
   * @memberof ValidationError
   */
  type: string
}
