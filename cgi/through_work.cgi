#!/usr/bin/perl
# 説明   : work をthrough する。
# 作成者 : 江野高広
# 作成日 : 2015/06/03

use strict;
use warnings;

use CGI;
use JSON;

use lib '/usr/local/TelnetmanWF/lib';
use Common_system;
use Common_sub;
use Access2DB;
use TelnetmanWF_common;

my $cgi = new CGI;

#
# DB アクセスのためのオブジェクトを作成する。
#
my ($DB_name, $DB_host, $DB_user, $DB_password) = &Common_system::DB_connect_parameter();
my @DB_connect_parameter_list                   = ('dbi:mysql:' . $DB_name . ':' . $DB_host, $DB_user, $DB_password);
my $access2db                                   = Access2DB -> open(@DB_connect_parameter_list);



#
# パスワードが正しいか確認。
#
my $ref_auth = &TelnetmanWF_common::authorize($cgi, $access2db);

if($ref_auth -> {'result'} == 0){
 my $json_results = &JSON::to_json($ref_auth);
 
 print "Content-type: text/plain; charset=UTF-8\n\n";
 print $json_results;
 
 $access2db -> close;
 
 exit(0);
}

my $flow_id = $ref_auth -> {'flow_id'};
my $task_id = $ref_auth -> {'task_id'};



my $work_id                  = $cgi -> param('work_id');
my $json_exec_node_list      = $cgi -> param('json_exec_node_list');
my $json_through_node_list   = $cgi -> param('json_through_node_list');



unless(defined($work_id) && (length($work_id) > 0)){
 print "Content-type: text/plain; charset=UTF-8\n\n";
 print '{"result":0,"reason":"Work ID がありません。"}';
 
 $access2db -> close;
 exit(0);
}



#
# パラメーターシートの有無確認。
#
my $file_parameter_sheet = &Common_system::file_parameter_sheet($flow_id, $task_id, $work_id);
 
unless(-f $file_parameter_sheet){
 print "Content-type: text/plain; charset=UTF-8\n\n";
 print '{"result":0,"reason":"パラメーターシートがありません。"}';
 
 $access2db -> close;
 exit(0);
}



#
# 流れ図があるかどうか確認する。
#
my $select_column = 'vcFlowchartBefore,vcFlowchartMiddle,vcFlowchartAfter';
my $table         = 'T_File';
my $condition     = "where vcFlowId = '" . $flow_id . "' and vcWorkId = '" . $work_id . "'";
$access2db -> set_select($select_column, $table, $condition);
my $ref_file_names = $access2db -> select_cols;

my $exists_flowchart_data = 1;
if((length($ref_file_names -> [0]) == 0) && (length($ref_file_names -> [1]) == 0) && (length($ref_file_names -> [2]) == 0)){
 $exists_flowchart_data = 0;
}



#
# through ノードの有無確認
#
my $ref_exec_node_list    = &JSON::from_json($json_exec_node_list);
my $ref_through_node_list = &JSON::from_json($json_through_node_list);

if(scalar(@$ref_through_node_list) == 0){
 my %results = (
  'result' => 1,
  'status' => 0,
  'flow_id' => $flow_id,
  'task_id' => $task_id,
  'work_id' => $work_id,
 'exists_flowchart_data' => $exists_flowchart_data
 );
 
 my $json_results = &JSON::to_json(\%results);
 
 print "Content-type: text/plain; charset=UTF-8\n\n";
 print $json_results;
 
 $access2db -> close;
 exit(0);
}



#
# 次の行き先を確認する。
#
$select_column = 'vcThroughTarget';
$table         = 'T_Work';
$condition     = "where vcFlowId = '" . $flow_id . "' and vcWorkId = '" . $work_id . "'";
$access2db -> set_select($select_column, $table, $condition);
my $json_through_target = $access2db -> select_col1;

my $ref_through_target = &JSON::from_json($json_through_target);
my $through_target_id = '';
if(exists($ref_through_target -> {'id'}) && ($ref_through_target -> {'id'} !~ /^start_/)){
 $through_target_id = $ref_through_target -> {'id'};
 
 my $dir_through_target = &Common_system::dir_log($flow_id, $task_id, $through_target_id);
 
 unless(-d $dir_through_target ){
  mkdir($dir_through_target , 0755)
 }
}



$access2db -> close;



my %results = (
 'result' => 1,
 'status' => 2,
 'flow_id' => $flow_id,
 'task_id' => $task_id,
 'work_id' => $work_id,
 'exists_flowchart_data' => $exists_flowchart_data,
 'exists_parameter_sheet' => 0,
 'target_list' => []
);



#
# パラメーターシートの分割
#
if(scalar(@$ref_exec_node_list) == 0){# 全ノードthrough
 if(length($through_target_id) > 0){# through 先有り
  open(PSHEET, '<', $file_parameter_sheet);
  my $json_parameter_sheet = <PSHEET>;
  close(PSHEET);
  
  my $file_parameter_sheet_through = &Common_system::file_parameter_sheet($flow_id, $task_id, $through_target_id);
  &TelnetmanWF_common::push_parameter_sheet($file_parameter_sheet_through, $json_parameter_sheet);
  push(@{$results{'target_list'}}, $through_target_id);
 }
 
 unlink($file_parameter_sheet);
}
else{# パラメーターシート分割
 open(PSHEET, '<', $file_parameter_sheet);
 my $json_parameter_sheet = <PSHEET>;
 close(PSHEET);
 
 my ($json_parameter_sheet_exec, $json_parameter_sheet_through) = &TelnetmanWF_common::extract_parameter_sheet($json_parameter_sheet, $ref_exec_node_list, $ref_through_node_list);
 
 if(length($through_target_id) > 0){# through 先有り
  my $file_parameter_sheet_through = &Common_system::file_parameter_sheet($flow_id, $task_id, $through_target_id);
  &TelnetmanWF_common::push_parameter_sheet($file_parameter_sheet_through, $json_parameter_sheet_through);
  push(@{$results{'target_list'}}, $through_target_id);
 }
 
 open(PSHEET, '>', $file_parameter_sheet);
 print PSHEET $json_parameter_sheet_exec;
 close(PSHEET);
 
 $results{'exists_parameter_sheet'} = 1;
 
 my ($ref_node_list, $ref_interface_list, $ref_node_info, $ref_interface_info, $error_message) = &TelnetmanWF_common::parse_parameter_sheet($json_parameter_sheet_exec);
 $results{'node_list'} = $ref_node_list;
}


my $json_results = &JSON::to_json(\%results);

print "Content-type: text/plain; charset=UTF-8\n\n";
print $json_results;